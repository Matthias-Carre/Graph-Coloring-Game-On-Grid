import random
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import torch
from torch.distributions import Categorical
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from game.Grid import Grid
from game.Alice.alice import Alice
from Model import GraphColoringNet

# ==========================================
# CONFIGURATION
# ==========================================
ALICE_MODE = "heuristic" 
LOGICS = ["random", "heuristic1", "nn"] 
ALICE_NN_PATH = str(Path(__file__).parent.parent / "checkpoints" / "Alice" / "latest.pt")

ALICE_PLAYER = 0
BOB_PLAYER = 1
DEBUG = False

class GraphColoringEnv(gym.Env):
    """
    Gymnasium environment for graph coloring game configured for Graph Neural Networks.
    """
    def __init__(self, width=3, height=3, num_colors=4):
        super(GraphColoringEnv, self).__init__()
        
        self.width = width
        self.height = height
        self.num_colors = num_colors
        self.total_nodes = width * height
        
        # Action space: choice of a cell and a color
        self.total_actions = self.total_nodes * self.num_colors
        self.action_space = spaces.Discrete(self.total_actions)
        
        # Features: One-hot encoded cell state (empty + colors) + Normalized X + Normalized Y
        self.num_features = (self.num_colors + 1) + 2
        
        self.observation_space = spaces.Dict({
            "observation": spaces.Box(
                low=0, high=1, 
                shape=(self.total_nodes, self.num_features), 
                dtype=np.float32
            ),
            "mask": spaces.Box(
                low=0, high=1, 
                shape=(self.total_actions,), 
                dtype=np.bool_ 
            )
        })
        
        self.grid = None
        self.Alice = None
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        self.move_history = []
        self.completed_episodes = []
        self.current_logic = None

        # Load Alice's neural network if required
        self.alice_nn = None
        if ALICE_MODE == "nn":
            self.alice_nn = GraphColoringNet(width=self.width, height=self.height, num_colors=self.num_colors)
            try:
                checkpoint = torch.load(ALICE_NN_PATH, map_location="cpu")
                self.alice_nn.load_state_dict(checkpoint["model_state_dict"])
                self.alice_nn.eval() 
                print(f"Environment initialized: Alice's NN successfully loaded from {ALICE_NN_PATH}")
            except FileNotFoundError:
                print(f"Warning: Alice's model not found at {ALICE_NN_PATH}. Falling back to heuristic.")
                self.alice_nn = None

    def _finish_episode(self, reason, reward):
        # Register episode metrics
        self.completed_episodes.append({
            "return": self.episode_return + reward,
            "length": self.episode_length,
            "reason": reason,
        })

    def _get_obs(self):
        # Generate node features for the Graph Transformer
        obs = np.zeros((self.total_nodes, self.num_features), dtype=np.float32)
        
        for j in range(self.height):
            for i in range(self.width):
                idx = j * self.width + i
                val = self.grid.get_cell(i, j).get_value()
                
                # One-hot encoding of the cell state
                obs[idx, val] = 1.0 
                
                # Spatial encoding coordinates
                obs[idx, -2] = i / max(1, self.width - 1)
                obs[idx, -1] = j / max(1, self.height - 1)
                
        return {
            "observation": obs,
            "mask": self.action_masks()
        }

    def _get_alice_nn_move(self):
        # Queries Alice's neural network for the next move
        obs_dict = self._get_obs()
        mask = obs_dict["mask"]
        
        valid_actions = [i for i, is_valid in enumerate(mask) if is_valid]
        if not valid_actions: 
            return None
            
        obs_tensor = torch.tensor(obs_dict["observation"], dtype=torch.float32).unsqueeze(0)
        mask_tensor = torch.tensor(mask, dtype=torch.bool).unsqueeze(0)
        
        with torch.no_grad():
            logits, _ = self.alice_nn(obs_tensor)
            logits = logits.masked_fill(~mask_tensor, -1e8)
            dist = Categorical(logits=logits)
            sampled_action = dist.sample().item()
            
        return self._action_to_move(sampled_action)

    def reset(self, seed=None, options=None):
        # Initialize episode state
        seed = seed or np.random.randint(0, 10000)
        super().reset(seed=seed)
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        self.move_history = []
        
        self.grid = Grid(self.height, self.width, self.num_colors)
        self.Alice = Alice(self.grid)
        self.grid.player = ALICE_PLAYER 
        self.current_logic = random.choice(LOGICS)
        
        # Execute Alice's opening move
        opening_move = None
        if ALICE_MODE == "nn" and self.alice_nn is not None:
            opening_move = self._get_alice_nn_move()
        else:
            if self.current_logic in ["random", "heuristic1", "nn"]:
                opening_move = self.Alice.next_random_move()
            
        if opening_move is not None:
            x, y, c = opening_move
            self.grid.play_move(x, y, c)
            self.move_history.append(('Alice', x, y, c))

        self.grid.player = BOB_PLAYER
        return self._get_obs(), {}

    def _action_to_move(self, action: int):
        # Decodes flat action index to spatial coordinates
        c = (action % self.num_colors) + 1
        cell_idx = action // self.num_colors
        x = cell_idx % self.width
        y = cell_idx // self.width
        return x, y, c
    
    def step(self, action):
        # Execute environment step
        self.current_step += 1
        self.episode_length += 1
        self.grid.player = BOB_PLAYER
        
        x, y, c = self._action_to_move(action)
        reward = 0.0

        if not self.grid.is_move_valid(x, y, c) or self.grid.get_cell(x, y).get_value() != 0:
            self._finish_episode("illegal_move", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "illegal_move"}

        p_num_safe_cells = self.count_safe_cells()
        self.grid.play_move(x, y, c)
        self.move_history.append(('Bob', x, y, c))
            
        n_num_safe_cells = self.count_safe_cells()

        if self.has_uncolorable_cell():
            self._finish_episode("bob_created_dead_node", 20.0)
            return self._get_obs(), 20.0, True, False, {"reason": "bob_created_dead_node"}

        if self.is_grid_full():
            self._finish_episode("bob_loses", -15.0)
            return self._get_obs(), -15.0, True, False, {"reason": "bob_loses"}

        self.grid.player = ALICE_PLAYER
        Alice_move = None
        epsilon = 0.2 
        
        if self.current_logic == "heuristic1" and random.random() >= epsilon:
            Alice_move = self.Alice.next_euristic1_move()
        elif self.current_logic == "nn" and self.alice_nn is not None:
            Alice_move = self._get_alice_nn_move()
        elif self.current_logic == "algo" and random.random() >= epsilon:
            Alice_move = self.Alice.next_move()
        else:
            Alice_move = self.Alice.next_random_move()
            
        if Alice_move is not None:
            alice_x, alice_y, alice_c = Alice_move
            self.grid.play_move(alice_x, alice_y, alice_c)
            self.move_history.append(('Alice', alice_x, alice_y, alice_c))
            
        self.grid.player = BOB_PLAYER

        if self.has_uncolorable_cell():
            self._finish_episode("alice_created_dead_node", 5.0)
            return self._get_obs(), 5.0, True, False, {"reason": "alice_created_dead_node"}

        if self.is_grid_full():
            self._finish_episode("bob_loses", -15.0)
            return self._get_obs(), -15.0, True, False, {"reason": "bob_loses"}

        self.episode_return += reward
        return self._get_obs(), reward, False, False, {}
    
    def action_masks(self):
        # Generate valid action boolean mask
        mask = np.zeros(self.total_actions, dtype=np.bool_)
        for i in range(self.width):
            for j in range(self.height):
                if self.grid.get_cell(i, j).get_value() == 0:
                    for c in range(self.num_colors):
                        color_to_test = c + 1
                        if self.grid.is_move_valid(i, j, color_to_test):
                            action_idx = (j * self.width + i) * self.num_colors + c
                            mask[action_idx] = True
        return mask

    def is_grid_full(self):
        for i in range(self.width):
            for j in range(self.height):
                if self.grid.get_cell(i, j).get_value() == 0:
                    return False
        return True
    
    def render(self):
        print(f"\n=== Tour {self.current_step} ===")
        player_color = {0: "\033[91m", 1: "\033[94m"}
        reset = "\033[0m"
        
        first_row = "  " + " ".join(str(i) for i in range(self.width))
        print(first_row)

        for j in range(self.height):
            row_str = f"{j} "
            for i in range(self.width):
                cell = self.grid.get_cell(i, j)
                val = cell.get_value()
                if val == 0:
                    row_str += ". "
                    continue
                color = player_color.get(cell.played_by, "")
                row_str += f"{color}{val}{reset} "
            print(row_str)
        print("===================")

    def count_safe_cells(self):
        count = 0
        for i in range(self.width):
            for j in range(self.height):
                cell = self.grid.get_cell(i, j)
                if cell.get_value() == 0 and cell.is_safe:
                    count += 1
        return count

    def count_color_critical_cells(self):
        count = 0
        for i in range(self.width):
            for j in range(self.height):
                cell = self.grid.get_cell(i, j)
                if cell.get_value() == 0 and cell.is_color_critical:
                    count += 1
        return count

    def has_uncolorable_cell(self):
        for i in range(self.width):
            for j in range(self.height):
                if self.grid.get_cell(i, j).get_value() == 0:
                    can_be_colored = False
                    for c in range(1, self.num_colors + 1):
                        if self.grid.is_move_valid(i, j, c):
                            can_be_colored = True
                            break 
                    if not can_be_colored:
                        return True 
        return False
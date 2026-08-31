import random
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import torch
from torch.distributions import Categorical
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from game.Grid import Grid
from game.Alice.alice import Alice
from Model import GraphColoringNet

# ==========================================
# TOGGLE ALICE'S BEHAVIOR HERE heuristic / nn / rand
# ==========================================

ALICE_MODE = "heuristic" 
#ALICE_MODE = "nn" 
LOGICS = ["random", "heuristic1"]  # List of available logics for Alice
#LOGICS = ["nn"]

ALICE_NN_PATH = str(Path(__file__).parent.parent / "checkpoints" / "Alice" / "latest.pt")

ALICE_PLAYER = 0
BOB_PLAYER = 1

DEBUG = False

class GraphColoringEnv(gym.Env):
    """
    Gymnasium environment for graph coloring game.
    """
    def __init__(self, width=3, height=3, num_colors=4):
        super(GraphColoringEnv, self).__init__()
        
        self.width = width
        self.height = height
        self.num_colors = num_colors
        
        
        # Action space: choice of a cell and a color
        # Total actions = (width * height) * number_of_colors
        self.total_actions = self.width * self.height * self.num_colors
        self.action_space = spaces.Discrete(self.total_actions)
        
        # Observation space in one-hot encoding
        # Format: (channels, height, width)
        # Channels: 1 for empty cells (0), then one channel per color
        self.observation_space = spaces.Dict({
            "observation": spaces.Box(
                low=0, high=1, 
                shape=(self.num_colors + 1, self.height, self.width), 
                dtype=np.float32
            ),
            "mask": spaces.Box(
                low=0, high=1, 
                shape=(self.total_actions,), 
                dtype=np.bool_ # Mask is a boolean array
            )
        })
        
        self.grid = None
        self.Alice = None
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        self.move_history = []
        self.completed_episodes = []

        # logic parameters
        self.current_logic = None

        # Load Alice's neural network if mode is active
        self.alice_nn = None
        if ALICE_MODE == "nn":
            self.alice_nn = GraphColoringNet(width=self.width, height=self.height, num_colors=self.num_colors)
            try:
                checkpoint = torch.load(ALICE_NN_PATH, map_location="cpu")
                self.alice_nn.load_state_dict(checkpoint["model_state_dict"])
                self.alice_nn.eval() # Freeze the network
                print(f"Environment initialized: Alice's NN successfully loaded from {ALICE_NN_PATH}")
            except FileNotFoundError:
                print(f"Warning: Alice's model not found at {ALICE_NN_PATH}. Falling back to heuristic.")
                self.alice_nn = None

    def _finish_episode(self, reason, reward):
        self.completed_episodes.append({
            "return": self.episode_return + reward,
            "length": self.episode_length,
            "reason": reason,
        })

    def _get_obs(self):
        obs = np.zeros((self.num_colors + 1, self.height, self.width), dtype=np.float32)
        
        for i in range(self.width):
            for j in range(self.height):
                val = self.grid.get_cell(i, j).get_value()
                # val is in [0, num_colors]
                obs[val, j, i] = 1.0 
                
        return {
            "observation": obs,
            "mask": self.action_masks()
        }

    def _get_alice_nn_move(self):
        """Queries the trained neural network for Alice's best move, combining epsilon-greedy with categorical sampling."""
        obs_dict = self._get_obs()
        mask = obs_dict["mask"]
        
        
        valid_actions = [i for i, is_valid in enumerate(mask) if is_valid]
        if valid_actions: 
            random_action = random.choice(valid_actions)
            return self._action_to_move(random_action)
        
        # Exploitation via sampling: play a move based on the neural network's probability distribution
        obs_tensor = torch.tensor(obs_dict["observation"], dtype=torch.float32).unsqueeze(0)
        mask_tensor = torch.tensor(mask, dtype=torch.bool).unsqueeze(0)
        
        with torch.no_grad():
            logits, _ = self.alice_nn(obs_tensor)
            logits = logits.masked_fill(~mask_tensor, -1e8)
            
            dist = Categorical(logits=logits)
            sampled_action = dist.sample().item()
            
        return self._action_to_move(sampled_action)

    def reset(self, seed=None, options=None):
        seed = seed or np.random.randint(0, 10000)
        super().reset(seed=seed)
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        self.move_history = []
        
        # Complete recreation of game state
        self.grid = Grid(self.height, self.width, self.num_colors)
        self.Alice = Alice(self.grid)

        self.grid.player = ALICE_PLAYER  # Alice starts first
        
        self.current_logic = random.choice(LOGICS)
        
        # Determine Alice's opening move based on selected mode
        opening_move = None
        if ALICE_MODE == "nn" and self.alice_nn is not None:
            opening_move = self._get_alice_nn_move()
        else:
            if self.current_logic == "random":
                opening_move = self.Alice.next_random_move()
            elif self.current_logic == "heuristic1":
                opening_move = self.Alice.next_random_move()
            elif self.current_logic == "nn" and self.alice_nn is not None:
                opening_move = self.Alice.next_random_move()
            
        if opening_move is not None:
            x, y, c = opening_move
            self.grid.play_move(x, y, c)
            self.move_history.append(('Alice', x, y, c))

        self.grid.player = BOB_PLAYER  # now it's Bob's turn
        
        return self._get_obs(), {}

    def _action_to_move(self, action: int):
        c = (action % self.num_colors) + 1
        cell_idx = action // self.num_colors
        x = cell_idx % self.width
        y = cell_idx // self.width
        return x, y, c
    
    
    def step(self, action):
        self.current_step += 1
        self.episode_length += 1
        
        self.grid.player = BOB_PLAYER
        c = (action % self.num_colors) + 1
        cell_idx = action // self.num_colors
        x = cell_idx % self.width
        y = cell_idx // self.width

        reward = 0.0
        terminated = False

        # --- Safety check ---
        if not self.grid.is_move_valid(x, y, c) or self.grid.get_cell(x, y).get_value() != 0:
            self._finish_episode("illegal_move", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "illegal_move"}

        # --- 1. Bob plays ---
        cc_cells = self.grid.get_number_of_dangerous_cc_cells()
        p_num_safe_cells = self.count_safe_cells()
        
        self.grid.play_move(x, y, c)
        self.move_history.append(('Bob', x, y, c))
        
        if DEBUG:
            print(f"Bob plays: ({x}, {y}, color {c})")
            self.render()
            
        n_num_safe_cells = self.count_safe_cells()

        # If Bob creates dead node -> Happy (he wins)
        if self.has_uncolorable_cell():
            if DEBUG:
                print("Bob created a dead node!")
            self._finish_episode("bob_created_dead_node", 20.0)
            #self.render()
            return self._get_obs(), 20.0, True, False, {"reason": "bob_created_dead_node"}

      
        # Did Bob win by filling the board? (He lost, Alice wins if grid is full and colorable)
        if self.is_grid_full():
            if DEBUG:
                print("Bob filled the last cell and lost!")
            self._finish_episode("bob_loses", -15.0)
            return self._get_obs(), -15.0, True, False, {"reason": "bob_loses"}

        # --- 2. Alice plays ---
        self.grid.player = ALICE_PLAYER
        
        # Determine Alice's move based on selected mode
        Alice_move = None
        
        epsilon = 0.2  # chance to play random
        
        if self.current_logic == "heuristic1" and random.random() >= epsilon:
            Alice_move = self.Alice.next_heuristic1_move()
        elif self.current_logic == "nn" and self.alice_nn is not None:
            Alice_move = self._get_alice_nn_move()
        elif self.current_logic == "algo" and random.random() >= epsilon:
            Alice_move = self.Alice.next_move()
                
        else:
        #elif self.current_logic == "random":
            Alice_move = self.Alice.next_random_move()
            
        if Alice_move is not None:
            alice_x, alice_y, alice_c = Alice_move
            self.grid.play_move(alice_x, alice_y, alice_c)
            self.move_history.append(('Alice', alice_x, alice_y, alice_c))
            
        self.grid.player = BOB_PLAYER

        # Check if Alice killed herself by creating a dead node
        if self.has_uncolorable_cell():
            if DEBUG:
                print("Alice created a dead node!")
            self._finish_episode("alice_created_dead_node", 5.0)
            #self.render()
            return self._get_obs(), 5.0, True, False, {"reason": "alice_created_dead_node"}

        # Did Alice fill last cell and win?
        if self.is_grid_full():
            if DEBUG:
                print("Alice filled the last cell and won!")
            self._finish_episode("bob_loses", -15.0)
            return self._get_obs(), -15.0, True, False, {"reason": "bob_loses"}

        self.episode_return += reward

        return self._get_obs(), reward, False, False, {}
    
    #version de steps pour essayer dautre score dans celle au dessus
    def step_backup(self, action):
        self.current_step += 1
        self.episode_length += 1
        
        self.grid.player = BOB_PLAYER
        c = (action % self.num_colors) + 1
        cell_idx = action // self.num_colors
        x = cell_idx % self.width
        y = cell_idx // self.width

        reward = 0.0
        terminated = False

        # --- Safety check ---
        if not self.grid.is_move_valid(x, y, c) or self.grid.get_cell(x, y).get_value() != 0:
            self._finish_episode("illegal_move", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "illegal_move"}

        # --- 1. Bob plays ---
        cc_cells = self.grid.get_number_of_dangerous_cc_cells()
        p_num_safe_cells = self.count_safe_cells()
        
        self.grid.play_move(x, y, c)
        self.move_history.append(('Bob', x, y, c))
        
        if DEBUG:
            print(f"Bob plays: ({x}, {y}, color {c})")
            self.render()
            
        n_num_safe_cells = self.count_safe_cells()

        # If Bob creates dead node -> Happy (he wins)
        if self.has_uncolorable_cell():
            if DEBUG:
                print("Bob created a dead node!")
            self._finish_episode("bob_created_dead_node", 20.0)
            return self._get_obs(), 20.0, True, False, {"reason": "bob_created_dead_node"}

        # Check if created safe cells -> Not very happy for Bob
        if n_num_safe_cells > p_num_safe_cells+1 :
            reward -= 0.2

        # Did Bob win by filling the board? (He lost, Alice wins if grid is full and colorable)
        if self.is_grid_full():
            if DEBUG:
                print("Bob filled the last cell and lost!")
            self._finish_episode("bob_loses", -15.0)
            return self._get_obs(), -15.0, True, False, {"reason": "bob_loses"}

        # --- 2. Alice plays ---
        self.grid.player = ALICE_PLAYER
        
        # Determine Alice's move based on selected mode
        Alice_move = None
        if ALICE_MODE == "nn" and self.alice_nn is not None:
            Alice_move = self._get_alice_nn_move()
        else:
            Alice_move = self.Alice.next_euristic1_move()
            
        if Alice_move is not None:
            alice_x, alice_y, alice_c = Alice_move
            self.grid.play_move(alice_x, alice_y, alice_c)
            self.move_history.append(('Alice', alice_x, alice_y, alice_c))
            
        self.grid.player = BOB_PLAYER

        # Check if Alice killed herself by creating a dead node
        if self.has_uncolorable_cell():
            if DEBUG:
                print("Alice created a dead node!")
            self._finish_episode("alice_created_dead_node", 5.0)
            return self._get_obs(), 5.0, True, False, {"reason": "alice_created_dead_node"}

        # Did Alice fill last cell and win?
        if self.is_grid_full():
            if DEBUG:
                print("Alice filled the last cell and won!")
            self._finish_episode("bob_loses", -15.0)
            return self._get_obs(), -15.0, True, False, {"reason": "bob_loses"}

        # For Bob, we dont want to reward surviving (time penalty)
        reward -= 0.2
        self.episode_return += reward

        return self._get_obs(), reward, False, False, {}
    
    
    def action_masks(self):
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
        player_color = {
            0: "\033[91m",
            1: "\033[94m",
        }
        reset = "\033[0m"
        
        first_row = ""
        for i in range(self.width):
            first_row += f"{i} "
        print(f"  {first_row}")

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


if __name__ == "__main__":
    print("Graph Coloring environment test...")
    env = GraphColoringEnv(width=8, height=4, num_colors=4)
    obs, info = env.reset()
    
    done = False
    total_reward = 0
    
    while not done:
        mask = env.action_masks()
        valid_actions = np.where(mask)[0]
        
        if len(valid_actions) == 0:
            print("No more legal actions!")
            break
            
        action = np.random.choice(valid_actions)
        
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        done = terminated or truncated

    print(f"\nGame ended. Total reward: {total_reward}")
    print(f"End reason: {info.get('reason', 'Unknown')}")
    
    print("\n--- FINAL GRID ---")
    env.render()
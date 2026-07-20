import random
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import torch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from game.Grid import Grid
from game.Bob.bob import Bob
from Model import GraphColoringNet

BOB_MODE = "heuristic" 
LOGICS = ["heuristic", "random", "nn"]

BOB_NN_PATH = str(Path(__file__).parent.parent / "checkpoints" / "Bob" / "latest.pt")

class GraphColoringEnv(gym.Env):
    def __init__(self, width=3, height=3, num_colors=4):
        super(GraphColoringEnv, self).__init__()
        
        self.width = width
        self.height = height
        self.num_colors = num_colors
        self.num_nodes = width * height
        
        self.total_actions = self.num_nodes * self.num_colors
        self.action_space = spaces.Discrete(self.total_actions)
        
        # MODIFIÉ : L'observation est maintenant une liste de nœuds (num_nodes, num_colors + 1)
        self.observation_space = spaces.Dict({
            "observation": spaces.Box(
                low=0, high=1, 
                shape=(self.num_nodes, self.num_colors + 1), 
                dtype=np.float32
            ),
            "mask": spaces.Box(
                low=0, high=1, 
                shape=(self.total_actions,), 
                dtype=np.bool_
            )
        })
        
        self.grid = None
        self.bob = None
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        self.completed_episodes = []

        self.bob_nn = None
        if BOB_MODE == "nn":
            self.bob_nn = GraphColoringNet(width=self.width, height=self.height, num_colors=self.num_colors)
            try:
                checkpoint = torch.load(BOB_NN_PATH, map_location="cpu")
                self.bob_nn.load_state_dict(checkpoint["model_state_dict"])
                self.bob_nn.eval()
                print(f"Environment initialized: Bob's NN successfully loaded")
            except FileNotFoundError:
                print(f"Warning: Bob's model not found. Falling back to heuristic.")
                self.bob_nn = None

    def _finish_episode(self, reason, reward):
        self.completed_episodes.append({
            "return": self.episode_return + reward,
            "length": self.episode_length,
            "reason": reason,
        })

    def _get_obs(self):
        # MODIFIÉ : On génère un tableau plat pour les nœuds au lieu d'une matrice 3D
        obs = np.zeros((self.num_nodes, self.num_colors + 1), dtype=np.float32)
        
        for j in range(self.height):
            for i in range(self.width):
                val = self.grid.get_cell(i, j).get_value()
                node_idx = j * self.width + i
                obs[node_idx, val] = 1.0 
                
        return {
            "observation": obs,
            "mask": self.action_masks()
        }


    def reset(self, seed=None, options=None):
        """Reinitializes environment at episode start."""
        seed = seed or np.random.randint(0, 10000)
        super().reset(seed=seed)
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        
        # Complete recreation of game state
        self.grid = Grid(self.height, self.width, self.num_colors)
        self.bob = Bob(self.grid)
        self.grid.player = 0  # Player 0 starts
        
        self.current_logic = random.choice(LOGICS)
        
        
        
        return self._get_obs(), {}

    def _action_to_move(self, action: int):
        """Converts action index to (x, y, color)."""
        c = (action % self.num_colors) + 1
        cell_idx = action // self.num_colors
        x = cell_idx % self.width
        y = cell_idx // self.width
        return x, y, c
    

    def _get_bob_nn_move(self):
        """Queries the trained neural network for Bob's best move, with epsilon-greedy randomness."""
        obs_dict = self._get_obs()
        
        # Epsilon-greedy: Play a random valid move with probability 'epsilon'
        
        mask = obs_dict["mask"]
        # Extract indices of all legal actions where the mask is True
        valid_actions = [i for i, is_valid in enumerate(mask) if is_valid]
            
        if valid_actions:  # Fallback check to ensure the list is not empty
            random_action = random.choice(valid_actions)
            #print(f"Bob: Played random move (epsilon {epsilon})") # Optional debug
            return self._action_to_move(random_action)
        
        # Exploitation: Play the best move according to the neural network
        obs_tensor = torch.tensor(obs_dict["observation"], dtype=torch.float32).unsqueeze(0)
        mask_tensor = torch.tensor(obs_dict["mask"], dtype=torch.bool).unsqueeze(0)
        
        with torch.no_grad():
            logits, _ = self.bob_nn(obs_tensor)
            # Penalize illegal moves
            logits = logits.masked_fill(~mask_tensor, -1e8)
            best_action = torch.argmax(logits, dim=1).item()
            
        return self._action_to_move(best_action)
    
    
    # Step with rewards only on lose or win
    def step(self, action):
        self.current_step += 1
        self.episode_length += 1
        
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

        # --- 1. Alice plays ---     
        self.grid.play_move(x, y, c)
        
        # Check if Alice created a dead node
        if self.has_uncolorable_cell():
            self._finish_episode("alice_created_dead_node", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "alice_created_dead_node"}

        # Did Alice win?
        if self.is_grid_full():
            self._finish_episode("alice_won", 10.0)
            return self._get_obs(), 10.0, True, False, {"reason": "alice_won"}

        # --- 2. Bob plays ---
        self.grid.player = 1
        
        # Determine Bob's move based on selected mode
        bob_move = None
        
        epsilon = 0.4
        
        if self.current_logic == "heuristic" and random.random() >= epsilon:
            bob_move = self.bob.next_move_euristic()
        elif self.current_logic == "nn" and self.bob_nn is not None :
            bob_move = self._get_bob_nn_move()
        else:
            bob_move = self.bob.next_random_move()
        
        if bob_move is not None:
            bob_x, bob_y, bob_c = bob_move
            self.grid.play_move(bob_x, bob_y, bob_c)
        self.grid.player = 0

        # Check if Bob created a dead node to trap Alice
        if self.has_uncolorable_cell():
            self._finish_episode("bob_created_dead_node", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "bob_created_dead_node"}

        # Did Alice win after Bob's move
        if self.is_grid_full():
            self._finish_episode("alice_won", 10.0)
            return self._get_obs(), 10.0, True, False, {"reason": "alice_won"}

        self.episode_return += reward
        return self._get_obs(), reward, False, False, {}
    
    # step_v2
    def step_v2(self, action):
        self.current_step += 1
        self.episode_length += 1
        
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

        # --- 1. Alice plays ---
        safe_count_before = self.count_safe_cells()
        color_critical_before = self.count_color_critical_cells()
        
        self.grid.play_move(x, y, c)
        
        # Check if Alice created a dead node
        if self.has_uncolorable_cell():
            self._finish_episode("alice_created_dead_node", -5.0)
            return self._get_obs(), -5.0, True, False, {"reason": "alice_created_dead_node"}

        # Count safe cells after move and award bonus
        safe_count_after = self.count_safe_cells()
        if safe_count_after > safe_count_before:
            safe_bonus = 1
        elif safe_count_after < safe_count_before:
            safe_bonus = -0.5
        else:
            safe_bonus = 0.0
        
        # Try: if E cc cell we want her to color it, else Bob will win
        color_critical_count = self.count_color_critical_cells()
        if color_critical_count < color_critical_before:
            safe_bonus += 3.0

        reward += safe_bonus

        # Did Alice win?
        if self.is_grid_full():
            self._finish_episode("alice_won", 20.0)
            return self._get_obs(), 20.0, True, False, {"reason": "alice_won"}

        # --- 2. Bob plays ---
        self.grid.player = 1
        
        # Determine Bob's move based on selected mode
        bob_move = None
        if BOB_MODE == "nn" and self.bob_nn is not None:
            bob_move = self._get_bob_nn_move()
        else:
            # bob_move = self.bob.next_move()
            bob_move = self.bob.next_random_move()
        
        if bob_move is not None:
            bob_x, bob_y, bob_c = bob_move
            self.grid.play_move(bob_x, bob_y, bob_c)
        self.grid.player = 0

        # Check if Bob created a dead node to trap Alice
        if self.has_uncolorable_cell():
            self._finish_episode("bob_created_dead_node", -20.0)
            return self._get_obs(), -10.0, True, False, {"reason": "bob_created_dead_node"}

        # Did Alice win after Bob's move
        if self.is_grid_full():
            self._finish_episode("alice_won", 15.0)
            return self._get_obs(), 15.0, True, False, {"reason": "alice_won"}

        reward += 0.2
        self.episode_return += reward
        return self._get_obs(), reward, False, False, {}

    def action_masks(self):
        """Returns boolean mask of legal actions."""
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
        """Indicates if all grid cells are colored."""
        for i in range(self.width):
            for j in range(self.height):
                if self.grid.get_cell(i, j).get_value() == 0:
                    return False
        return True
    
    def render(self):
        """Displays current grid state in terminal."""
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
        """Counts empty cells marked as safe."""
        count = 0
        for i in range(self.width):
            for j in range(self.height):
                cell = self.grid.get_cell(i, j)
                if cell.get_value() == 0 and cell.is_safe:
                    count += 1
        return count

    def count_color_critical_cells(self):
        """Counts empty cells that are color-critical (only one color possible)."""
        count = 0
        for i in range(self.width):
            for j in range(self.height):
                cell = self.grid.get_cell(i, j)
                if cell.get_value() == 0 and cell.is_color_critical:
                    count += 1
        return count

    def has_uncolorable_cell(self):
        """Iterates through all empty cells to check for dead nodes."""
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
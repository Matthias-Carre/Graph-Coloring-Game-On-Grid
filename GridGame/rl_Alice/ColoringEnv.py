import gymnasium as gym
from gymnasium import spaces
import numpy as np
import sys
from pathlib import Path
import torch

# Add the parent directory to the import path.
sys.path.insert(0, str(Path(__file__).parent.parent))

from game.Grid import Grid
# The old heuristic Bob import was removed.
# Make sure the path to your model is correct.
from Model import GraphColoringNet 

class GraphColoringEnv(gym.Env):
    """
    Gymnasium environment for graph coloring game with AI Bob.
    """
    def __init__(self, width=3, height=3, num_colors=4, bob_model=None):
        super(GraphColoringEnv, self).__init__()
        
        self.width = width
        self.height = height
        self.num_colors = num_colors
        
        # Bob's PyTorch model.
        self.bob_model = bob_model
        if self.bob_model is not None:
            self.bob_model.eval()  # Always keep the model in evaluation mode.
        
        # Action space: one choice per cell-color pair.
        self.total_actions = self.width * self.height * self.num_colors
        self.action_space = spaces.Discrete(self.total_actions)
        
        # Observation space in one-hot encoding.
        self.observation_space = spaces.Dict({
            "observation": spaces.Box(
                low=0, high=1, 
                shape=(self.num_colors + 1, self.height, self.width), 
                dtype=np.float32
            ),
            "mask": spaces.Box(
                low=0, high=1, 
                shape=(self.total_actions,), 
                dtype=np.bool_
            )
        })
        
        self.grid = None
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        self.completed_episodes = []

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
                obs[val, j, i] = 1.0 
                
        return {
            "observation": obs,
            "mask": self.action_masks()
        }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        
        self.grid = Grid(self.height, self.width, self.num_colors)
        self.grid.player = 0
        
        return self._get_obs(), {}

    def _action_to_move(self, action: int):
        c = (action % self.num_colors) + 1
        cell_idx = action // self.num_colors
        x = cell_idx % self.width
        y = cell_idx // self.width
        return x, y, c
    
    def _get_bob_action(self):
        """Demande au réseau de neurones de Bob de choisir une action."""
        obs_dict = self._get_obs()
        mask = obs_dict["mask"]
        
        # S'il n'y a plus aucune action légale, Bob ne peut pas jouer
        if not np.any(mask):
            return None
            
        # Si un modèle est fourni, on l'utilise
        if self.bob_model is not None:
            obs_tensor = torch.tensor(obs_dict["observation"], dtype=torch.float32).unsqueeze(0)
            mask_tensor = torch.tensor(mask, dtype=torch.bool).unsqueeze(0)
            
            with torch.no_grad():
                logits, _ = self.bob_model(obs_tensor)
                logits = logits.masked_fill(~mask_tensor, -1e8)
                best_action = torch.argmax(logits, dim=1).item()
            return best_action
            
        # Fallback de sécurité : s'il n'y a pas de modèle, Bob joue au hasard
        valid_actions = np.where(mask)[0]
        return np.random.choice(valid_actions)
    
    # Keep only step() for clarity.
    # Apply the same change to step_v1 if needed.
    def step(self, action):
        self.current_step += 1
        self.episode_length += 1
        
        x, y, c = self._action_to_move(action)
        reward = 0.0

        # --- Safety check ---
        if not self.grid.is_move_valid(x, y, c) or self.grid.get_cell(x, y).get_value() != 0:
            self._finish_episode("illegal_move", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "illegal_move"}

        # --- 1. Alice plays ---
        safe_count_before = self.count_safe_cells()
        color_critical_before = self.count_color_critical_cells()
        
        self.grid.play_move(x, y, c)
        
        if self.has_uncolorable_cell():
            self._finish_episode("alice_created_dead_node", -20.0)
            return self._get_obs(), -20.0, True, False, {"reason": "alice_created_dead_node"}

        safe_count_after = self.count_safe_cells()
        if safe_count_after > safe_count_before:
            safe_bonus = 1
        elif safe_count_after < safe_count_before:
            safe_bonus = -0.5
        else:
            safe_bonus = 0.0
        
        color_critical_count = self.count_color_critical_cells()
        if color_critical_count < color_critical_before:
            safe_bonus += 3.0

        reward += safe_bonus

        if self.is_grid_full():
            self._finish_episode("alice_won", 15.0)
            return self._get_obs(), 15.0, True, False, {"reason": "alice_won"}

        # --- 2. Bob plays (AI) ---
        self.grid.player = 1
        bob_action = self._get_bob_action()
        
        if bob_action is not None:
            bob_x, bob_y, bob_c = self._action_to_move(bob_action)
            self.grid.play_move(bob_x, bob_y, bob_c)
            
        self.grid.player = 0

        if self.has_uncolorable_cell():
            self._finish_episode("bob_created_dead_node", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "bob_created_dead_node"}

        if self.is_grid_full():
            self._finish_episode("alice_won", 15.0)
            return self._get_obs(), 15.0, True, False, {"reason": "alice_won"}

        reward += 0.2
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
        player_color = {0: "\033[91m", 1: "\033[94m"}
        reset = "\033[0m"
        
        first_row = ""
        for i in range(self.width): first_row += f"{i} "
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
                if cell.get_value() == 0 and cell.is_safe: count += 1
        return count

    def count_color_critical_cells(self):
        count = 0
        for i in range(self.width):
            for j in range(self.height):
                cell = self.grid.get_cell(i, j)
                if cell.get_value() == 0 and cell.is_color_critical: count += 1
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
                    if not can_be_colored: return True
        return False

# --- TEST SCRIPT ---
if __name__ == "__main__":
    print("Graph Coloring environment test...")
    
    WIDTH, HEIGHT, COLORS = 5, 5, 4 
    
    # 1. Load Bob's brain.
    script_dir = Path(__file__).parent.parent
    MODEL_PATH = str(script_dir / "checkpoints" / "Bob" / "latest.pt")
    
    try:
        bob_brain = GraphColoringNet(width=WIDTH, height=HEIGHT, num_colors=COLORS)
        checkpoint = torch.load(MODEL_PATH, map_location="cpu")
        bob_brain.load_state_dict(checkpoint["model_state_dict"])
        print("Bob's brain loaded successfully!")
    except FileNotFoundError:
        print(f"Warning: The file {MODEL_PATH} was not found. Bob will play randomly.")
        bob_brain = None

    # 2. Initialize the environment with the loaded model.
    env = GraphColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS, bob_model=bob_brain)
    obs, info = env.reset()
    
    done = False
    total_reward = 0
    
    while not done:
        mask = env.action_masks()
        valid_actions = np.where(mask)[0]
        
        if len(valid_actions) == 0:
            print("No more legal actions!")
            break
            
        action = np.random.choice(valid_actions)  # Alice still plays randomly here.
        
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        done = terminated or truncated
        
        env.render() 

    print(f"\nGame ended. Total reward: {total_reward}")
    print(f"End reason: {info.get('reason', 'Unknown')}")
import gymnasium as gym
from gymnasium import spaces
import numpy as np


from game.Grid import Grid
from game.Bob.bob import Bob

class GraphColoringEnv(gym.Env):
    """
    Gymnasium environment for graph coloring game.
    """
    def __init__(self, width=5, height=4, num_colors=4):
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
        self.bob = None
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        self.completed_episodes = []

    def _finish_episode(self, reason, reward):
        """Store the completed episode statistics for later logging."""
        self.completed_episodes.append({
            "return": self.episode_return + reward,
            "length": self.episode_length,
            "reason": reason,
        })

    def _get_obs(self):
        """Converts grid state to one-hot tensor (C+1, H, W)."""
        obs = np.zeros((self.num_colors + 1, self.height, self.width), dtype=np.float32)
        
        for i in range(self.width):
            for j in range(self.height):
                val = self.grid.get_cell(i, j).get_value()
                # val est dans [0, num_colors]
                obs[val, j, i] = 1.0 
                
        return {
            "observation": obs,
            "mask": self.action_masks()
        }

    def reset(self, seed=None, options=None):
        """Reinitializes environment at episode start."""
        super().reset(seed=seed)
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        
        # Complete recreation of game state
        self.grid = Grid(self.height, self.width, self.num_colors)
        self.bob = Bob(self.grid)
        self.grid.player = 0  # Player 0 starts
        
        return self._get_obs(), {}


    def _action_to_move(self, action: int):
        """Converts action index to (x, y, color)."""
        c = (action % self.num_colors) + 1
        cell_idx = action // self.num_colors
        x = cell_idx % self.width
        y = cell_idx // self.width
        return x, y, c
    
    
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
            #print(f"ColoringEnv: Illegal move attempted at ({x}, {y}) with color {c}.")
            self._finish_episode("illegal_move", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "illegal_move"}

        # --- 1. Alice plays ---     
        self.grid.play_move(x, y, c)
        
        # Check if Alice created a dead node
        # Alice should NEVER create a dead node == giving the win to Bob (unless last move possible)
        if self.has_uncolorable_cell():
            self._finish_episode("alice_created_dead_node", -20.0)
            return self._get_obs(), -20.0, True, False, {"reason": "alice_created_dead_node"}

        # Did Alice win?
        if self.is_grid_full():
            self._finish_episode("alice_won", 15.0)
            return self._get_obs(), 15.0, True, False, {"reason": "alice_won"}

        # --- 2. Bob plays ---
        self.grid.player = 1
        bob_move = self.bob.next_move()
        if bob_move is not None:
            bob_x, bob_y, bob_c = bob_move
            self.grid.play_move(bob_x, bob_y, bob_c)
        self.grid.player = 0

        # Check if Bob created a dead node to trap Alice
        if self.has_uncolorable_cell():
            self._finish_episode("bob_created_dead_node", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "bob_created_dead_node"}

        # Did Alice win after Bob's move (rare but possible if Bob fills last cell)
        if self.is_grid_full():
            self._finish_episode("alice_won", 15.0)
            return self._get_obs(), 15.0, True, False, {"reason": "alice_won"}

        # Survival reward + safe bonus already included
        reward += 0.2
        self.episode_return += reward
        return self._get_obs(), reward, False, False, {}
    

    def step_backup(self, action):
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
            #print(f"ColoringEnv: Illegal move attempted at ({x}, {y}) with color {c}.")
            self._finish_episode("illegal_move", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "illegal_move"}

        # --- 1. Alice plays ---

        # Count safe cells before move
        safe_count_before = self.count_safe_cells()
        color_critical_before = self.count_color_critical_cells()
        #print(f"Step {self.current_step}: nmb of safe before: {safe_count_before}")
        
        self.grid.play_move(x, y, c)
        
        # Check if Alice created a dead node
        # Alice should NEVER create a dead node == giving the win to Bob (unless last move possible)
        if self.has_uncolorable_cell():
            self._finish_episode("alice_created_dead_node", -20.0)
            return self._get_obs(), -20.0, True, False, {"reason": "alice_created_dead_node"}

        # Count safe cells after move and award bonus
        # Intuition: Alice should try to make the most cells safe every move 
        safe_count_after = self.count_safe_cells()
        #print(f"Step {self.current_step}: nmb of safe after: {safe_count_after}")
        if safe_count_after > safe_count_before:
            #print(f"Alice created safe cells! ")
            safe_bonus = 1
        elif safe_count_after < safe_count_before:
            safe_bonus = -0.5
        else:
            safe_bonus = 0.0
        

        # Try : if E cc cell we want her to color it, else Bob will win
        color_critical_count = self.count_color_critical_cells()
        if color_critical_count < color_critical_before:
            #print(f"Alice created color-critical cells! ")
            safe_bonus += 3.0


        reward += safe_bonus

        # Did Alice win?
        if self.is_grid_full():
            self._finish_episode("alice_won", 15.0)
            return self._get_obs(), 15.0, True, False, {"reason": "alice_won"}

        # --- 2. Bob plays ---
        self.grid.player = 1
        bob_move = self.bob.next_move()
        if bob_move is not None:
            bob_x, bob_y, bob_c = bob_move
            self.grid.play_move(bob_x, bob_y, bob_c)
        self.grid.player = 0

        # Check if Bob created a dead node to trap Alice
        if self.has_uncolorable_cell():
            self._finish_episode("bob_created_dead_node", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "bob_created_dead_node"}

        # Did Alice win after Bob's move (rare but possible if Bob fills last cell)
        if self.is_grid_full():
            self._finish_episode("alice_won", 15.0)
            return self._get_obs(), 15.0, True, False, {"reason": "alice_won"}

        # Survival reward + safe bonus already included
        reward += 0.2
        self.episode_return += reward
        return self._get_obs(), reward, False, False, {}




    def action_masks(self):
        """Returns boolean mask of legal actions."""
        # np.bool_ is kept for Gymnasium/TorchRL compatibility
        mask = np.zeros(self.total_actions, dtype=np.bool_)
        
        for i in range(self.width):
            for j in range(self.height):
                # Action only possible on empty cell
                if self.grid.get_cell(i, j).get_value() == 0:
                    for c in range(self.num_colors):
                        color_to_test = c + 1
                        # Verify color legality on cell
                        if self.grid.is_move_valid(i, j, color_to_test):
                            # Reverse conversion (x, y, color) -> action index
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
        
        # Display color based on player who colored cell
        # Alice (0): red, Bob (1): blue
        player_color = {
            0: "\033[91m",
            1: "\033[94m",
        }
        reset = "\033[0m"
        
        # Iterate row by row
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
        """
        Iterates through all empty cells.
        Returns True if any cell accepts no more colors.
        """
        for i in range(self.width):
            for j in range(self.height):
                # Only check empty cells
                if self.grid.get_cell(i, j).get_value() == 0:
                    can_be_colored = False
                    for c in range(1, self.num_colors + 1):
                        if self.grid.is_move_valid(i, j, c):
                            can_be_colored = True
                            break # At least one color is possible, move to next cell
                    
                    # If all colors tested and none valid
                    if not can_be_colored:
                        return True # Node is dead
        return False


if __name__ == "__main__":
    print("Graph Coloring environment test...")
    # Reduced size for easier console reading
    env = GraphColoringEnv(width=8, height=4, num_colors=4)
    obs, info = env.reset()
    
    done = False
    total_reward = 0
    
    # Optionnel : affichage de l'état initial
    # env.render() 
    
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
        
        # Optional: display after each move
        # env.render() 

    print(f"\nGame ended. Total reward: {total_reward}")
    print(f"End reason: {info.get('reason', 'Unknown')}")
    
    # Display final grid
    print("\n--- FINAL GRID ---")
    env.render()
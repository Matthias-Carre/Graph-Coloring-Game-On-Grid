import gymnasium as gym
from gymnasium import spaces
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from game.Grid import Grid
from game.Alice.alice import Alice

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
        self.completed_episodes = []

    #store the episode statistics to keep track 
    def _finish_episode(self, reason, reward):
        self.completed_episodes.append({
            "return": self.episode_return + reward,
            "length": self.episode_length,
            "reason": reason,
        })

    #convert the grid format to a one-hot encoding for the neural network input
    def _get_obs(self):
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

    #reinitializes the environement to start a new episode
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        
        # Complete recreation of game state
        self.grid = Grid(self.height, self.width, self.num_colors)
        self.Alice = Alice(self.grid)

        self.grid.player = ALICE_PLAYER  # Alice starts first
        opening_move = self.Alice.next_random_move()
        if opening_move is not None:
            x, y, c = opening_move
            self.grid.play_move(x, y, c)

        self.grid.player = BOB_PLAYER  # now it's Bob's turn
        
        return self._get_obs(), {}

    # Converts an action index to its corresponding move (x, y, color).
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
            #print(f"ColoringEnv: Illegal move attempted at ({x}, {y}) with color {c}.")
            self._finish_episode("illegal_move", -10.0)
            return self._get_obs(), -10.0, True, False, {"reason": "illegal_move"}

        # --- 1. Bob plays ---
        #cc_cells = self.grid.get_number_of_cc_cells()
        cc_cells = self.grid.get_number_of_dangerous_cc_cells()
        p_num_safe_cells = self.count_safe_cells()
        self.grid.play_move(x, y, c)
        if DEBUG:
            print(f"Bob plays: ({x}, {y}, color {c})")
            self.render()
        n_num_safe_cells = self.count_safe_cells()
        # Check for Bob rewards

        #if create dead node Happy
        if self.has_uncolorable_cell():
            if DEBUG:
                print("Bob created a dead node!")
            self._finish_episode("bob_created_dead_node", 20.0)
            return self._get_obs(), 20.0, True, False, {"reason": "bob_created_dead_node"}

        #check if create safe cells not verry happy 
        if n_num_safe_cells > p_num_safe_cells+1 :
            reward -= 0.2

        #if create Color-Critical node Happy
        #if cc_cells < self.count_color_critical_cells():
        #    reward += 0.2

        #if cc before and bob dose not create dead not happy
        if cc_cells > 0 and not self.has_uncolorable_cell():
            if DEBUG:
                print("Bob missed an opportunity to create a dead node!")
            reward -= 0.5



        # Did Alice win?
        if self.is_grid_full():
            if DEBUG:
                print("Bob filled the last cell and lost!")
            self._finish_episode("bob_loses", -15.0)
            return self._get_obs(), -15.0, True, False, {"reason": "bob_loses"}

        # --- 2. Alice plays ---
        self.grid.player = ALICE_PLAYER
        Alice_move = self.Alice.next_safe_move()
        if Alice_move is not None:
            alice_x, alice_y, alice_c = Alice_move
            self.grid.play_move(alice_x, alice_y, alice_c)
        self.grid.player = BOB_PLAYER

        # Check if Alice kill herself by creating a dead node
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

        # Survival reward + safe bonus already included
        #For Bob, we dont want to reward surviving
        reward -= 0.2
        self.episode_return += reward

        return self._get_obs(), reward, False, False, {}
    

    # return the mask of legal actions for the current grid state.
    def action_masks(self):
        
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

    # check if every cell is colored
    def is_grid_full(self):
        
        for i in range(self.width):
            for j in range(self.height):
                if self.grid.get_cell(i, j).get_value() == 0:
                    return False
        
        return True
    
    # quick desplay of the grid in the terminal
    def render(self):

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

    # return the nu;ber of safe cells
    def count_safe_cells(self):
        count = 0
        for i in range(self.width):
            for j in range(self.height):
                cell = self.grid.get_cell(i, j)
                if cell.get_value() == 0 and cell.is_safe:
                    count += 1
        return count

    # return the num of cells that could become uncolorable
    def count_color_critical_cells(self):
        count = 0
        for i in range(self.width):
            for j in range(self.height):
                cell = self.grid.get_cell(i, j)
                if cell.get_value() == 0 and cell.is_color_critical:
                    count += 1
        return count

    # check for empty cells taht have no remaining legal color 
    def has_uncolorable_cell(self):
        
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
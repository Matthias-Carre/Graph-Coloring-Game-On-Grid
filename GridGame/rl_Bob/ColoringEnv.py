import random
import numpy as np
import torch
import torch.nn.functional as F
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from game.Grid import Grid
from game.Alice.alice import Alice
# IMPERATIF : Importer le nouveau modèle DQN
from model import GraphColoringDQN 

# ==========================================
# TOGGLE ALICE'S BEHAVIOR HERE heuristic / nn / random
# ==========================================
ALICE_MODE = "heuristic" 
LOGICS = ["random", "heuristic1", "nn"] # List of available logics for Alice

ALICE_NN_PATH = str(Path(__file__).parent.parent / "checkpoints" / "Alice" / "latest.pt")

ALICE_PLAYER = 0
BOB_PLAYER = 1

DEBUG = False

class ColoringEnv:
    """
    Environment for graph coloring game adapted for GNN + DQN.
    """
    def __init__(self, width=3, height=3, num_colors=4):
        self.width = width
        self.height = height
        self.num_colors = num_colors
        
        self.num_nodes = width * height
        self.num_classes = num_colors + 1
        self.total_actions = self.num_nodes * self.num_colors
        
        # Construction des arêtes du graphe une seule fois à l'initialisation
        self.edge_index = self._build_grid_edges()
        
        self.grid = None
        self.Alice = None
        self.current_step = 0
        self.episode_return = 0.0
        self.episode_length = 0
        self.move_history = []
        self.completed_episodes = []

        self.current_logic = None

        # Load Alice's neural network if mode is active
        self.alice_nn = None
        if ALICE_MODE == "nn":
            self.alice_nn = GraphColoringDQN(num_node_features=self.num_classes, hidden_size=64, num_colors=self.num_colors)
            try:
                checkpoint = torch.load(ALICE_NN_PATH, map_location="cpu")
                self.alice_nn.load_state_dict(checkpoint["model_state_dict"])
                self.alice_nn.eval() # Freeze the network
                print(f"Environment initialized: Alice's NN successfully loaded from {ALICE_NN_PATH}")
            except Exception as e:
                print(f"Warning: Could not load Alice's model properly ({e}). Falling back to heuristic.")
                self.alice_nn = None

    def _build_grid_edges(self):
        """Construit la topologie de la grille pour le GNN."""
        edges = []
        for y in range(self.height):
            for x in range(self.width):
                node = y * self.width + x
                # Voisin de droite
                if x < self.width - 1:
                    right = node + 1
                    edges.append([node, right])
                    edges.append([right, node])
                # Voisin du bas
                if y < self.height - 1:
                    bottom = node + self.width
                    edges.append([node, bottom])
                    edges.append([bottom, node])
        return torch.tensor(edges, dtype=torch.long).t().contiguous()

    def _finish_episode(self, reason, reward):
        self.completed_episodes.append({
            "return": self.episode_return + reward,
            "length": self.episode_length,
            "reason": reason,
        })

    def _get_obs(self):
        """Transforme l'état du jeu en format GNN (One-Hot, Edge Index, Mask)"""
        flat_grid = []
        for y in range(self.height):
            for x in range(self.width):
                flat_grid.append(self.grid.get_cell(x, y).get_value())
                
        state_tensor = torch.tensor(flat_grid, dtype=torch.long)
        x_tensor = F.one_hot(state_tensor, num_classes=self.num_classes).float()
        
        mask = torch.tensor(self.action_masks(), dtype=torch.bool)
        
        return {
            "x": x_tensor,
            "edge_index": self.edge_index,
            "mask": mask
        }

    def _get_alice_nn_move(self):
        """Demande au DQN d'Alice de trouver le meilleur coup."""
        obs_dict = self._get_obs()
        mask_tensor = obs_dict["mask"]
        
        valid_actions = torch.where(mask_tensor)[0]
        if len(valid_actions) == 0:
            return None
            
        with torch.no_grad():
            q_values = self.alice_nn(obs_dict["x"], obs_dict["edge_index"])
            # Masquer les coups illégaux
            masked_q_values = q_values.masked_fill(~mask_tensor, float('-inf'))
            # Alice joue le coup avec la Q-value maximale
            best_action = masked_q_values.argmax().item()
            
        return self._action_to_move(best_action)

    def reset(self):
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
        
        return self._get_obs()

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
        x, y, c = self._action_to_move(action)

        reward = 0.0

        # --- Safety check ---
        if not self.grid.is_move_valid(x, y, c) or self.grid.get_cell(x, y).get_value() != 0:
            self._finish_episode("illegal_move", -10.0)
            return self._get_obs(), -10.0, True

        # --- 1. Bob plays ---
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
            return self._get_obs(), 20.0, True

        # Check if created safe cells -> Not very happy for Bob
        if n_num_safe_cells > p_num_safe_cells + 1:
            reward -= 0.2

        # Did Bob win by filling the board? (He lost, Alice wins if grid is full and colorable)
        if self.is_grid_full():
            if DEBUG:
                print("Bob filled the last cell and lost!")
            self._finish_episode("bob_loses", -15.0)
            return self._get_obs(), -15.0, True

        # --- 2. Alice plays ---
        self.grid.player = ALICE_PLAYER
        
        Alice_move = None
        epsilon = 0.2  # chance to play random
        
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

        # Check if Alice killed herself by creating a dead node
        if self.has_uncolorable_cell():
            if DEBUG:
                print("Alice created a dead node!")
            self._finish_episode("alice_created_dead_node", 5.0)
            return self._get_obs(), 5.0, True

        # Did Alice fill last cell and win?
        if self.is_grid_full():
            if DEBUG:
                print("Alice filled the last cell and won!")
            self._finish_episode("bob_loses", -15.0)
            return self._get_obs(), -15.0, True

        # Time penalty
        reward -= 0.2
        self.episode_return += reward

        return self._get_obs(), reward, False
    
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
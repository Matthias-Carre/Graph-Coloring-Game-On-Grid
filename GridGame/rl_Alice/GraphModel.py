import gymnasium as gym
from gymnasium import spaces
import numpy as np
import torch

class GraphColoringEnv(gym.Env):
    """
    Gymnasium environment for Graph Coloring (Alice vs Bob).
    Alice acts via PPO, Bob acts via built-in random/heuristic response.
    """
    def __init__(self, width=3, height=3, num_colors=4):
        super(GraphColoringEnv, self).__init__()
        
        self.width = width
        self.height = height
        self.num_colors = num_colors
        self.num_nodes = width * height
        
        # Action space: all possible node-color combinations
        self.total_actions = self.num_nodes * self.num_colors
        self.action_space = spaces.Discrete(self.total_actions)
        
        # Observation space formatted for Graph Neural Networks
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
        
        self.state = None
        self.edge_index = self._build_grid_edges()

    def _build_grid_edges(self):
        # Create bidirectional edge list for a 2D grid topology
        edges = []
        for y in range(self.height):
            for x in range(self.width):
                node = y * self.width + x
                if x > 0: edges.append([node, node - 1])
                if x < self.width - 1: edges.append([node, node + 1])
                if y > 0: edges.append([node, node - self.width])
                if y < self.height - 1: edges.append([node, node + self.width])
        
        return torch.tensor(edges, dtype=torch.long).t().contiguous()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Initialize board with -1 (empty)
        self.state = np.full(self.num_nodes, -1, dtype=np.int32)
        return self._get_obs(), {}

    def _get_obs(self):
        # Generate one-hot encoded node features
        obs = np.zeros((self.num_nodes, self.num_colors + 1), dtype=np.float32)
        for i in range(self.num_nodes):
            val = self.state[i]
            if val == -1:
                obs[i, self.num_colors] = 1.0  # Empty state
            else:
                obs[i, val] = 1.0
                
        return {
            "observation": obs,
            "mask": self._get_action_masks()
        }

    def _is_valid(self, node, color):
        # Check if color is legal by inspecting neighbors
        for i in range(self.edge_index.shape[1]):
            u = self.edge_index[0, i].item()
            v = self.edge_index[1, i].item()
            if u == node and self.state[v] == color:
                return False
        return True

    def _get_action_masks(self):
        # Generate boolean mask for legal moves
        mask = np.zeros(self.total_actions, dtype=np.bool_)
        for node in range(self.num_nodes):
            if self.state[node] == -1:
                for c in range(self.num_colors):
                    if self._is_valid(node, c):
                        mask[node * self.num_colors + c] = True
        return mask

    def step(self, action):
        color = action % self.num_colors
        node = action // self.num_colors

        # Apply Alice's move
        self.state[node] = color
        
        if self._is_grid_full():
            return self._get_obs(), 10.0, True, False, {"reason": "alice_won"}
            
        if self._has_uncolorable_cell():
            return self._get_obs(), -10.0, True, False, {"reason": "alice_lost"}

        # Apply Bob's random legal response
        self._bob_random_move()
        
        if self._has_uncolorable_cell():
            return self._get_obs(), -10.0, True, False, {"reason": "bob_created_dead_node"}
            
        if self._is_grid_full():
            return self._get_obs(), 10.0, True, False, {"reason": "bob_filled_last"}

        # Step survival reward
        return self._get_obs(), 1.0, False, False, {}

    def _bob_random_move(self):
        # Select a random valid action for the opponent
        mask = self._get_action_masks()
        valid_actions = np.where(mask)[0]
        if len(valid_actions) > 0:
            action = np.random.choice(valid_actions)
            self.state[action // self.num_colors] = action % self.num_colors

    def _is_grid_full(self):
        return not np.any(self.state == -1)

    def _has_uncolorable_cell(self):
        # Check if any empty cell has no legal colors left
        for node in range(self.num_nodes):
            if self.state[node] == -1:
                can_color = False
                for c in range(self.num_colors):
                    if self._is_valid(node, c):
                        can_color = True
                        break
                if not can_color:
                    return True
        return False
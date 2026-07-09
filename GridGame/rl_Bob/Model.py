import torch
import torch.nn as nn
from torch_geometric.nn import GINConv
import torch.nn.functional as F

class GraphColoringDQN(nn.Module):
    def __init__(self, num_node_features, hidden_size, num_colors):
        super(GraphColoringDQN, self).__init__()
        
        self.num_colors = num_colors
        
        # Define the MLP for the first GIN layer
        mlp1 = nn.Sequential(
            nn.Linear(num_node_features, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size)
        )
        self.gin1 = GINConv(mlp1)
        
        # Define the MLP for the second GIN layer
        mlp2 = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size)
        )
        self.gin2 = GINConv(mlp2)
        
        # Linear head projecting hidden features to Q-values for each color
        self.q_head = nn.Linear(hidden_size, num_colors)

    def forward(self, x, edge_index):
        # Extract topological embeddings
        h = self.gin1(x, edge_index)
        h = F.relu(h)
        h = self.gin2(h, edge_index)
        h = F.relu(h)
        
        # Compute Q-values per node
        # Output shape: [num_nodes, num_colors]
        q_values_per_node = self.q_head(h)
        
        # Flatten to match the 1D action space: [num_nodes * num_colors]
        q_values_flat = q_values_per_node.view(-1)
        
        return q_values_flat
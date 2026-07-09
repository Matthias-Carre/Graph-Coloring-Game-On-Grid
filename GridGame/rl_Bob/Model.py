import torch
import torch.nn as nn
from torch_geometric.nn import GINConv
import torch.nn.functional as F

class GraphColoringDQN(nn.Module):
    def __init__(self, num_node_features, hidden_size, num_colors):
        super(GraphColoringDQN, self).__init__()
        
        self.num_colors = num_colors
        
        # Define MLP for first GIN layer
        mlp1 = nn.Sequential(
            nn.Linear(num_node_features, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size)
        )
        self.gin1 = GINConv(mlp1)
        
        # Define MLP for second GIN layer
        mlp2 = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size)
        )
        self.gin2 = GINConv(mlp2)
        
        # Linear head for Q-values
        self.q_head = nn.Linear(hidden_size, num_colors)

    def forward(self, x, edge_index, batch_size=1):
        # Extract topological embeddings
        h = self.gin1(x, edge_index)
        h = F.relu(h)
        h = self.gin2(h, edge_index)
        h = F.relu(h)
        
        # Compute Q-values per node
        q_values_per_node = self.q_head(h)
        
        # Reshape to keep batch dimension separate from actions
        return q_values_per_node.view(batch_size, -1)
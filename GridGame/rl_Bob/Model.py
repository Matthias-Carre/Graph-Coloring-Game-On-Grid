import torch
import torch.nn as nn
from torch_geometric.nn import TransformerConv
import torch.nn.functional as F

class GraphColoringTransformer(nn.Module):
    def __init__(self, num_node_features, hidden_size, num_colors, num_heads=4):
        super(GraphColoringTransformer, self).__init__()
        self.num_colors = num_colors
        
        # Configure transformer to accept 1D edge attributes
        self.conv1 = TransformerConv(
            in_channels=num_node_features, 
            out_channels=hidden_size // num_heads, 
            heads=num_heads, 
            edge_dim=1, 
            dropout=0.1
        )
        
        self.conv2 = TransformerConv(
            in_channels=hidden_size, 
            out_channels=hidden_size // num_heads, 
            heads=num_heads, 
            edge_dim=1, 
            dropout=0.1
        )
        
        self.head = nn.Linear(hidden_size, num_colors)

    def forward(self, x, edge_index, edge_attr, batch_size=1):
        # Inject structural distances into attention computations
        h = self.conv1(x, edge_index, edge_attr=edge_attr)
        h = F.relu(h)
        
        h = self.conv2(h, edge_index, edge_attr=edge_attr)
        h = F.relu(h)
        
        scores_per_node = self.head(h)
        return scores_per_node.view(batch_size, -1)
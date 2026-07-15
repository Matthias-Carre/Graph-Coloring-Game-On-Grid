import torch
import torch.nn as nn
from torch_geometric.nn import GINConv, TransformerConv, global_mean_pool
import torch.nn.functional as F

class GraphColoringDQN(nn.Module):
    # Legacy architecture used by Alice
    def __init__(self, num_node_features, hidden_size, num_colors):
        super(GraphColoringDQN, self).__init__()
        self.num_colors = num_colors
        
        mlp1 = nn.Sequential(
            nn.Linear(num_node_features, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size)
        )
        self.gin1 = GINConv(mlp1)
        
        mlp2 = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size)
        )
        self.gin2 = GINConv(mlp2)
        
        self.q_head = nn.Linear(hidden_size, num_colors)

    def forward(self, x, edge_index, batch_size=1):
        h = self.gin1(x, edge_index)
        h = F.relu(h)
        h = self.gin2(h, edge_index)
        h = F.relu(h)
        q_values_per_node = self.q_head(h)
        return q_values_per_node.view(batch_size, -1)


class GraphColoringTransformerPPO(nn.Module):
    # Actor-Critic architecture using multi-head attention and spatial encoding
    def __init__(self, num_node_features, hidden_size, num_colors, num_heads=4):
        super(GraphColoringTransformerPPO, self).__init__()
        self.num_colors = num_colors
        
        # Transformer blocks with 1D edge attribute support
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
        
        # Actor head outputs action logits
        self.actor_head = nn.Linear(hidden_size, num_colors)
        
        # Critic head outputs a single graph value
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, x, edge_index, edge_attr, batch_index=None, batch_size=1):
        # Extract features using spatial attention
        h = self.conv1(x, edge_index, edge_attr=edge_attr)
        h = F.relu(h)
        h = self.conv2(h, edge_index, edge_attr=edge_attr)
        h = F.relu(h)
        
        # Compute action probabilities
        logits_per_node = self.actor_head(h)
        logits = logits_per_node.view(batch_size, -1)
        
        # Evaluate global board state
        if batch_index is None:
            batch_index = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
            
        graph_embed = global_mean_pool(h, batch_index)
        value = self.critic_head(graph_embed)
        
        return logits, value
import torch
import torch.nn as nn
from torch_geometric.nn import TransformerConv, global_mean_pool

class GraphColoringNet(nn.Module):
    """
    Graph Transformer Actor-Critic architecture for PPO.
    """
    def __init__(self, width, height, num_colors, hidden_dim=64, num_layers=3):
        super().__init__()
        self.num_colors = num_colors
        self.num_nodes = width * height
        num_node_features = num_colors + 1
        
        # Project initial sparse features to dense latent space
        self.encoder = nn.Linear(num_node_features, hidden_dim)
        
        # Graph Transformer layers for message passing
        self.transformer_layers = nn.ModuleList()
        for _ in range(num_layers):
            self.transformer_layers.append(
                TransformerConv(
                    in_channels=hidden_dim, 
                    out_channels=hidden_dim // 4, 
                    heads=4, 
                    concat=True
                )
            )
            
        # Actor head: Outputs preference scores (logits) for each color
        self.actor_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_colors)
        )
        
        # Critic head: Evaluates the overall quality of the graph state
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, x, edge_index, mask=None, batch_index=None):
        # Encode nodes
        h = torch.relu(self.encoder(x))
        
        # Apply self-attention message passing
        for conv in self.transformer_layers:
            h = torch.relu(conv(h, edge_index))
            
        # Compute actor logits and flatten
        node_logits = self.actor_head(h)
        actor_logits = node_logits.view(-1) 
        
        # Apply action mask if provided (replace invalid with strong negative)
        if mask is not None:
            actor_logits = actor_logits.masked_fill(~mask, -1e8)
            
        # Pool node embeddings to compute global graph value
        if batch_index is None:
            batch_index = torch.zeros(h.size(0), dtype=torch.long, device=h.device)
            
        global_h = global_mean_pool(h, batch_index)
        critic_value = self.critic_head(global_h)
        
        return actor_logits, critic_value
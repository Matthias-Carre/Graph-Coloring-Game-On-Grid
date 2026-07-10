import torch
import torch.nn as nn
from torch_geometric.nn import GINConv, global_mean_pool
import torch.nn.functional as F

class GraphColoringDQN(nn.Module):
    # Retained for Alice's backward compatibility
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


class GraphColoringPPO(nn.Module):
    # Actor-Critic architecture for PPO
    def __init__(self, num_node_features, hidden_size, num_colors):
        super(GraphColoringPPO, self).__init__()
        self.num_colors = num_colors
        
        # Shared GNN backbone
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
        
        # Actor head: Outputs logits for action probabilities
        self.actor_head = nn.Linear(hidden_size, num_colors)
        
        # Critic head: Outputs a single value evaluating the whole graph state
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, x, edge_index, batch_index=None, batch_size=1):
        # Extract topological embeddings
        h = self.gin1(x, edge_index)
        h = F.relu(h)
        h = self.gin2(h, edge_index)
        h = F.relu(h)
        
        # Actor: Compute logits per node and flatten
        logits_per_node = self.actor_head(h)
        logits = logits_per_node.view(batch_size, -1)
        
        # Critic: Pool node embeddings to evaluate the entire board
        if batch_index is None:
            batch_index = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
            
        graph_embed = global_mean_pool(h, batch_index)
        value = self.critic_head(graph_embed)
        
        return logits, value
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import TransformerConv, global_mean_pool

class GraphColoringNet(nn.Module):
    """
    Actor-Critic Graph Transformer Architecture.
    Bridges standard tensor batches to PyTorch Geometric dynamic graphs.
    """
    def __init__(self, width, height, num_colors, hidden_size=64, num_heads=4):
        super(GraphColoringNet, self).__init__()
        self.width = width
        self.height = height
        self.num_colors = num_colors
        self.num_nodes = width * height
        
        # Features: (Empty + Colors) + Norm_X + Norm_Y
        in_channels = (num_colors + 1) + 2
        
        # Precompute fully connected edges and normalized Manhattan distances
        edges = []
        edge_attrs = []
        max_dist = (width - 1) + (height - 1)
        
        for y1 in range(height):
            for x1 in range(width):
                node1 = y1 * width + x1
                for y2 in range(height):
                    for x2 in range(width):
                        node2 = y2 * width + x2
                        edges.append([node1, node2])
                        dist = abs(x1 - x2) + abs(y1 - y2)
                        norm_dist = dist / max_dist if max_dist > 0 else 0.0
                        edge_attrs.append([norm_dist])
                        
        # Register as buffers so they move to the correct device automatically
        self.register_buffer("base_edge_index", torch.tensor(edges, dtype=torch.long).t().contiguous())
        self.register_buffer("base_edge_attr", torch.tensor(edge_attrs, dtype=torch.float32))
        
        # Transformer Multi-Head Attention layers
        self.conv1 = TransformerConv(in_channels, hidden_size // num_heads, heads=num_heads, edge_dim=1, dropout=0.0)
        self.conv2 = TransformerConv(hidden_size, hidden_size // num_heads, heads=num_heads, edge_dim=1, dropout=0.0)
        
        # Actor Head outputs logits for every cell * num_colors
        self.actor_head = nn.Linear(hidden_size, num_colors)
        
        # Critic Head evaluates global board state
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, observation):
        # Handle unbatched observations
        has_batch = observation.dim() == 3
        if not has_batch:
            observation = observation.unsqueeze(0)
            
        B, N, num_features = observation.shape
        device = observation.device
        
        x = observation.view(B * N, num_features)
        
        # Dynamically duplicate the topology for the entire batch
        E = self.base_edge_index.size(1)
        offsets = torch.arange(0, B * N, N, device=device).view(B, 1, 1)
        batched_edge_index = (self.base_edge_index.unsqueeze(0) + offsets).transpose(0, 1).reshape(2, B * E)
        batched_edge_attr = self.base_edge_attr.repeat(B, 1)
        
        # Spatial feature extraction
        h = self.conv1(x, batched_edge_index, edge_attr=batched_edge_attr)
        h = F.relu(h)
        h = self.conv2(h, batched_edge_index, edge_attr=batched_edge_attr)
        h = F.relu(h)
        
        # ACTOR: Compute action probabilities
        logits_per_node = self.actor_head(h)
        logits = logits_per_node.view(B, N * self.num_colors)
        
        # CRITIC: Pool node embeddings to evaluate the entire graph
        batch_index = torch.arange(B, device=device).repeat_interleave(N)
        graph_embed = global_mean_pool(h, batch_index)
        value = self.critic_head(graph_embed)
        
        if not has_batch:
            logits = logits.squeeze(0)
            value = value.squeeze(0)
            
        return logits, value
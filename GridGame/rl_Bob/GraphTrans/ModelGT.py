import torch
import torch.nn as nn
from torch_geometric.nn import TransformerConv, global_mean_pool

class GraphColoringNet(nn.Module):
    def __init__(self, width, height, num_colors, hidden_dim=64, num_layers=3):
        super().__init__()
        
        self.width = width
        self.height = height
        self.num_colors = num_colors
        self.num_nodes = width * height
        in_channels = num_colors + 1
        
        # Encodeur initial
        self.encoder = nn.Linear(in_channels, hidden_dim)
        
        # Couches Graph attention-based
        self.gnn_layers = nn.ModuleList()
        for _ in range(num_layers):
            self.gnn_layers.append(
                TransformerConv(
                    in_channels=hidden_dim, 
                    out_channels=hidden_dim // 4, 
                    heads=4, 
                    concat=True
                )
            )
            
        # Tête de l'Acteur (Décide la couleur de chaque case)
        self.actor_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_colors)
        )
        
        # Tête du Critique (Évalue la qualité globale de la grille)
        self.critic_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, observation, edge_index):
        # Gestion du format Batch imposé par TorchRL
        add_batch = observation.dim() == 2
        if add_batch:
            observation = observation.unsqueeze(0)
            
        B, N, C = observation.shape
        
        # Projection initiale
        h = torch.relu(self.encoder(observation)) 
        
        # ASTUCE PYG : On aplatit le batch de graphes en un seul "méga-graphe" déconnecté
        h_flat = h.view(B * N, -1)
        
        # On duplique les arêtes pour chaque graphe du batch
        E = edge_index.size(1)
        batch_offsets = torch.arange(B, device=observation.device).view(-1, 1) * N
        
        
        batched_edge_index = edge_index.unsqueeze(0) + batch_offsets.unsqueeze(-1)
        # On transpose d'abord pour séparer proprement la ligne des sources et des cibles
        batched_edge_index = batched_edge_index.transpose(0, 1).reshape(2, B * E)
        
        # Passage dans les couches GNN
        for conv in self.gnn_layers:
            h_flat = torch.relu(conv(h_flat, batched_edge_index))
            
        # Calcul de l'Acteur
        actor_logits = self.actor_head(h_flat)
        actor_logits = actor_logits.view(B, N * self.num_colors) # On reformate en [Batch, Toutes_Les_Actions]
        
        # Calcul du Critique (Global Pooling)
        batch_idx = torch.arange(B, device=observation.device).repeat_interleave(N)
        global_h = global_mean_pool(h_flat, batch_idx)
        value = self.critic_head(global_h)
        
        if add_batch:
            actor_logits = actor_logits.squeeze(0)
            value = value.squeeze(0)
            
        return actor_logits, value
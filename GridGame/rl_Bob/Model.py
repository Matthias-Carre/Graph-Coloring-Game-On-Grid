import torch
import torch.nn as nn

class GraphColoringNet(nn.Module):
    """
    Shared actor-critic network for the grid coloring task.
    """
    def __init__(self, width, height, num_colors):
        super(GraphColoringNet, self).__init__()
        
        self.width = width
        self.height = height
        self.num_colors = num_colors
        
        in_channels = num_colors + 1
        
        # Shared convolutional feature extractor.
        self.shared_cnn = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU()
        )
        
        
        # Size of flattened convolutional features.
        self.flattened_size = 64 * height * width
        
        
        # Policy head.
        self.actor_head = nn.Sequential(
            nn.Linear(self.flattened_size, 128),
            nn.ReLU(),
            nn.Linear(128, width * height * num_colors)
        )
        
        # Value head.
        self.critic_head = nn.Sequential(
            nn.Linear(self.flattened_size, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

    def forward(self, observation):
        # Convolutional features, shape: (batch, channels, height, width).
        features = self.shared_cnn(observation)
        
        # Flatten all dimensions except batch.
        features_flat = features.view(-1, self.flattened_size) 
        
        # Compute policy logits and state value.
        logits = self.actor_head(features_flat)
        value = self.critic_head(features_flat)
        
        return logits, value
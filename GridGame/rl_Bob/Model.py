import torch
import torch.nn as nn
from e2cnn import gspaces
from e2cnn import nn as enn

class GraphColoringNet(nn.Module):
    """
    Shared actor-critic network for the grid coloring task.
    Updated with Equivariant Steerable CNNs (escnn).
    """
    def __init__(self, width, height, num_colors):
        super(GraphColoringNet, self).__init__()
        
        self.width = width
        self.height = height
        self.num_colors = num_colors
        
        in_channels = num_colors + 1
        
        # Define the symmetry group for 4 discrete rotations (0, 90, 180, 270 degrees)
        self.r2_act = gspaces.Rot2dOnR2(N=4)
        
        # Define input type: standard scalar fields (trivial representation)
        self.in_type = enn.FieldType(self.r2_act, in_channels * [self.r2_act.trivial_repr])
        
        # Define hidden type: regular representation
        # A regular representation over N=4 has size 4. 
        # To maintain 64 channels, we use 16 regular representations (16 * 4 = 64).
        self.hidden_type = enn.FieldType(self.r2_act, 16 * [self.r2_act.regular_repr])
        
        # Shared equivariant convolutional feature extractor
        self.shared_cnn = enn.SequentialModule(
            enn.R2Conv(self.in_type, self.hidden_type, kernel_size=3, padding=1),
            enn.ReLU(self.hidden_type, inplace=True),
            enn.R2Conv(self.hidden_type, self.hidden_type, kernel_size=3, padding=1),
            enn.ReLU(self.hidden_type, inplace=True)
        )
        
        # Size of flattened convolutional features (16 * 4 = 64 channels)
        self.flattened_size = 64 * height * width
        
        # Policy head
        self.actor_head = nn.Sequential(
            nn.Linear(self.flattened_size, 128),
            nn.ReLU(),
            nn.Linear(128, width * height * num_colors)
        )
        
        # Value head
        self.critic_head = nn.Sequential(
            nn.Linear(self.flattened_size, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

    def forward(self, observation):
        # e2cnn strictly requires a 4D tensor (Batch, Channels, Height, Width).
        # TorchRL sometimes passes unbatched 3D tensors during collector setup.
        add_batch = observation.dim() == 3
        if add_batch:
            observation = observation.unsqueeze(0)
            
        # Wrap the PyTorch tensor into a GeometricTensor
        x = enn.GeometricTensor(observation, self.in_type)
        
        # Extract features using equivariant convolutions
        features = self.shared_cnn(x)
        
        # Unwrap back to a standard PyTorch tensor
        # The shape is now (batch, 64, height, width)
        features_flat = features.tensor.view(-1, self.flattened_size) 
        
        # Compute policy logits and state value
        logits = self.actor_head(features_flat)
        value = self.critic_head(features_flat)
        
        # Remove the artificial batch dimension if we added it
        if add_batch:
            logits = logits.squeeze(0)
            value = value.squeeze(0)
            
        return logits, value
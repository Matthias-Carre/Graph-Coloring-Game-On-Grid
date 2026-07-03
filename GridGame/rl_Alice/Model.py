import torch
import torch.nn as nn
from escnn import gspaces
from escnn import nn as enn

class GraphColoringNet(nn.Module):
    def __init__(self, width, height, num_colors):
        super(GraphColoringNet, self).__init__()
        
        self.width = width
        self.height = height
        self.num_colors = num_colors
        
        in_channels = num_colors + 1
        
        # Define symmetry group for 4 discrete rotations.
        self.r2_act = gspaces.flipRot2dOnR2(N=4)
        self.r2_act = gspaces.flipRot2dOnR2(N=4)
        
        self.in_type = enn.FieldType(self.r2_act, in_channels * [self.r2_act.trivial_repr])
        self.hidden_type = enn.FieldType(self.r2_act, 32 * [self.r2_act.regular_repr])
        
        # Shared equivariant convolutional feature extractor.
        self.shared_cnn = enn.SequentialModule(
            enn.R2Conv(self.in_type, self.hidden_type, kernel_size=3, padding=1),
            enn.ReLU(self.hidden_type, inplace=True),
            
            enn.R2Conv(self.hidden_type, self.hidden_type, kernel_size=3, padding=1),
            enn.ReLU(self.hidden_type, inplace=True),
            
            enn.R2Conv(self.hidden_type, self.hidden_type, kernel_size=3, padding=1),
            enn.ReLU(self.hidden_type, inplace=True)
        )
        
        # ==========================================
        # THE ACTOR HEAD (Equivariant)
        # ==========================================
        # The output must be num_colors. Colors don't rotate (Color 1 is always Color 1), 
        # so we use trivial representations.
        self.out_type = enn.FieldType(self.r2_act, self.num_colors * [self.r2_act.trivial_repr])
        
        # We use 1x1 convolutions to maintain spatial awareness instead of nn.Linear
        self.actor_head = enn.SequentialModule(
            enn.R2Conv(self.hidden_type, self.hidden_type, kernel_size=1),
            enn.ReLU(self.hidden_type, inplace=True),
            enn.R2Conv(self.hidden_type, self.out_type, kernel_size=1)
        )
        
        # ==========================================
        # THE CRITIC HEAD (Invariant)
        # ==========================================
        # The Critic just needs to know if the board is good/bad, it shouldn't care about rotation.
        # GroupPooling extracts rotation-invariant features safely.
        #self.group_pool = enn.GroupPooling(self.hidden_type)
        
        self.critic_flattened_size = 32 * height * width
        
        
        # After pooling, we have 32 channels.
        self.critic_flattened_size = 32 * height * width
        
        self.critic_head = nn.Sequential(
            nn.Linear(self.critic_flattened_size, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

    def forward(self, observation):
        add_batch = observation.dim() == 3
        if add_batch:
            observation = observation.unsqueeze(0)
            
        x = enn.GeometricTensor(observation, self.in_type)
        features = self.shared_cnn(x)
        
        # --- ACTOR ---
        # Output shape is (Batch, num_colors, Height, Width)
        actor_geom = self.actor_head(features)
        actor_tensor = actor_geom.tensor 
        
        # CRITICAL TRICK: We permute the dimensions to (Batch, Height, Width, num_colors)
        # This matches the Gymnasium action mapping: action = (y * width + x) * num_colors + c
        actor_tensor = actor_tensor.permute(0, 2, 3, 1).contiguous()
        
        # Now we flatten it safely into (Batch, 100). The geometry correctly maps to the action indices!
        logits = actor_tensor.view(actor_tensor.size(0), -1)
        
        # --- CRITIC ---
        # Pool the rotation states manually to make the board evaluation strictly invariant.
        # We avoid escnn's GroupPooling here because its in-place operations conflict with TorchRL's vmap.
        
        # features.tensor shape is (Batch, 128, Height, Width)
        # We have 32 representations, each consisting of 8 rotation channels.
        raw_critic_tensor = features.tensor
        B, C, H, W = raw_critic_tensor.shape
        
        # Reshape to isolate the 4 rotations: (Batch, 32, 4, Height, Width)
        # 8 for D4
        reshaped_tensor = raw_critic_tensor.view(B, 32, 8, H, W)
        # Reshape to isolate the 8 rotations: (Batch, 32, 8, Height, Width)
        reshaped_tensor = raw_critic_tensor.view(B, 32, 8, H, W)
        
        # Take the maximum over the rotation dimension (dim=2) to achieve invariance
        # The result shape is (Batch, 32, Height, Width)
        invariant_tensor, _ = reshaped_tensor.max(dim=2)
        
        critic_flat = invariant_tensor.view(-1, self.critic_flattened_size)
        value = self.critic_head(critic_flat)
        
        if add_batch:
            logits = logits.squeeze(0)
            value = value.squeeze(0)
            
        return logits, value
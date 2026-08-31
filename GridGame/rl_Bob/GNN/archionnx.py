import torch

from ModelGNN import GraphColoringNet


# Instantiate the model architecture
model = GraphColoringNet(width=5, height=5, num_colors=4)
model.eval()

# Remove or comment out this line! It is not needed for Netron visualization.
# model.load_state_dict(checkpoint["model_state_dict"]) 

# Create dummy inputs with correct shapes
dummy_obs = torch.randn(1, 25, 5) 
dummy_edge_index = torch.tensor([
    [0, 1, 1, 2], 
    [1, 0, 2, 1]
], dtype=torch.long)

# Export the model graph to ONNX
torch.onnx.export(
    model,
    (dummy_obs, dummy_edge_index),
    "gnn_architecture.onnx",
    export_params=True,
    opset_version=14,
    do_constant_folding=True,
    input_names=['Observation_Grille', 'Edge_Index'],
    output_names=['Logits_Actor', 'Value_Critic']
)

print("Export ONNX successful!")
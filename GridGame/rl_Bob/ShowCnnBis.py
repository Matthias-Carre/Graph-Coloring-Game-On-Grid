import torch
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# Add the parent directory to the path to import local modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from Model import GraphColoringNet

def create_trap_observation(width, height, num_colors):
    """
    Manually creates the observation (One-hot encoded) for a specific setup:
    An empty cell in the center, surrounded by colors 1, 2, and 3.
    """
    # Initialization: set all cells to "empty" state (channel 0)
    obs = np.zeros((num_colors + 1, height, width), dtype=np.float32)
    obs[0, :, :] = 1.0 
    
    center_x, center_y = width // 2, height // 2
    
    # Place Color 1 at the top
    obs[0, center_y - 1, center_x] = 0.0 # No longer empty
    obs[1, center_y - 1, center_x] = 1.0 # Set to color 1
    
    # Place Color 2 on the left
    obs[0, center_y, center_x - 1] = 0.0
    obs[2, center_y, center_x - 1] = 1.0
    
    # Place Color 3 on the right
    obs[0, center_y, center_x + 1] = 0.0
    obs[3, center_y, center_x + 1] = 1.0
    
    return obs

def matrix_to_obs(matrix, num_colors=4):
    """
    Translates a 2D matrix (list of lists) into a tensor observation (Channels, H, W).
    0 = empty, 1-4 = colors.
    """
    # Ensure we are working with a NumPy array
    grid = np.array(matrix)
    height, width = grid.shape
    
    # Create an empty tensor filled with zeros
    obs = np.zeros((num_colors + 1, height, width), dtype=np.float32)
    
    # Fill the tensor: for each cell, set a "1" on the corresponding color channel
    for y in range(height):
        for x in range(width):
            val = grid[y, x]
            obs[val, y, x] = 1.0
            
    return obs


def main():
    WIDTH, HEIGHT, COLORS = 5, 5, 4

    matrice = [[0, 0, 0, 0, 0],
               [0, 0, 3, 0, 0],
               [0, 1, 0, 0, 0],
               [0, 0, 2, 0, 0],
               [0, 0, 0, 0, 0]]
    
    # 1. Create the observation and convert it for PyTorch
    obs_numpy = matrix_to_obs(matrice, COLORS)
    obs_tensor = torch.tensor(obs_numpy).unsqueeze(0) # Add batch dimension: [1, 5, 5, 5]
    
    # 2. Load Bob's brain (model weights)
    script_dir = Path(__file__).parent.parent
    MODEL_PATH = str(script_dir / "Models" / "Bob4x4.pt")
    
    model = GraphColoringNet(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    try:
        checkpoint = torch.load(MODEL_PATH, map_location="cpu")
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        print("Model loaded successfully. Extracting Feature Maps...")
    except FileNotFoundError:
        print(f"File {MODEL_PATH} not found. The network will be initialized randomly (untrained).")
    
    # 3. LAYER EXTRACTION
    # Extract the first four sequential blocks: Conv1 -> ReLU1 -> Conv2 -> ReLU2
    second_conv_block = model.shared_cnn[:4]
    
    with torch.no_grad():
        # Pass the observation tensor through the extracted sequence
        activated_features = second_conv_block(obs_tensor)
        
    # Remove the batch dimension for plotting: the shape becomes [64, H, W]
    feature_maps = activated_features.squeeze(0).numpy()
    
    # 4. PLOT FEATURE MAPS (Matplotlib)
    # Create an 8x8 grid to display all 64 feature maps
    fig, axes = plt.subplots(8, 8, figsize=(16, 16))
    fig.suptitle(f"64 Feature Maps of the 2nd Layer", fontsize=16)
    
    # Find the global maximum activation value to normalize the colors
    vmax = np.max(feature_maps)
    
    for i, ax in enumerate(axes.flat):
        # Extract the 2D grid for channel i
        fmap = feature_maps[i]
        
        # Display with a heatmap (using 'magma' colormap)
        im = ax.imshow(fmap, cmap='magma', vmin=0, vmax=vmax)
        ax.set_title(f"Filter {i}")
        ax.axis('off') # Hide X and Y axes for clarity
        
    # Add a colorbar legend for the activation levels
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    fig.colorbar(im, cax=cbar_ax, label="Activation level (Signal)")
    
    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.show()

if __name__ == "__main__":
    main()
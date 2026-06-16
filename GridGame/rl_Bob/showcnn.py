import torch
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import sys
from pathlib import Path

# Add the parent directory to the path (as in your original code)
sys.path.insert(0, str(Path(__file__).parent.parent))

from Model import GraphColoringNet

def create_trap_observation(width, height, num_colors):
    """
    Manually creates the observation (One-hot) for your specific setup:
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
    
    # Fill the tensor: for each cell, set a "1" on the correct color channel
    for y in range(height):
        for x in range(width):
            val = grid[y, x]
            obs[val, y, x] = 1.0
            
    return obs


def main():
    WIDTH, HEIGHT, COLORS = 5, 5, 4

    matrice = [[0, 0, 1, 0, 0],
               [0, 2, 0, 3, 0],
               [0, 0, 0, 1, 0],
               [0, 0, 2, 0, 3],
               [0, 0, 0, 0, 0]]
    
    # 1. Observation creation and PyTorch conversion
    obs_numpy = matrix_to_obs(matrice, COLORS)
    obs_tensor = torch.tensor(obs_numpy).unsqueeze(0) # Add the batch dimension: [1, 5, 5, 5]
    
    # 2. Loading Bob's brain
    script_dir = Path(__file__).parent.parent
    MODEL_PATH = str(script_dir / "Models" / "Bob8x8.pt")
    MODEL_PATH = str(script_dir / "checkpoints" / "Bob" / "latest.pt")
    
    model = GraphColoringNet(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    try:
        checkpoint = torch.load(MODEL_PATH, map_location="cpu")
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        print("Model loaded successfully. Extracting Feature Maps...")
    except FileNotFoundError:
        print(f"File {MODEL_PATH} not found. The network will be initialized randomly (untrained).")
    
    # 3. SURGICAL EXTRACTION
    # Instead of doing model(obs_tensor), we isolate the first Conv layer + ReLU
    # In your init: self.shared_cnn[0] is the Conv2d, self.shared_cnn[1] is the ReLU
    first_conv_layer = model.shared_cnn[0]
    first_relu = model.shared_cnn[1]
    
    with torch.no_grad():
        # Pass the data only through this small part of the network
        raw_features = first_conv_layer(obs_tensor)
        activated_features = first_relu(raw_features)
        
    # Remove the batch dimension for displaying: the shape becomes [32, H, W]
    feature_maps = activated_features.squeeze(0).numpy()
    
    # 4. DISPLAYING THE INPUT GRID AND 32 FEATURE MAPS (Matplotlib)
    # Create a figure with a custom grid layout (4 rows, 9 columns)
    fig = plt.figure(figsize=(18, 8))
    fig.suptitle(f"Input Context & 32 Feature Maps of the 1st Layer (3x3 Filters)", fontsize=16)
    
    # GridSpec allows us to allocate the first column for the input and the rest for feature maps
    gs = fig.add_gridspec(4, 9, width_ratios=[1.2, 1, 1, 1, 1, 1, 1, 1, 1])
    
    # --- A. Plotting the Input Matrix ---
    # Span the middle two rows (index 1 and 2) of the first column
    ax_input = fig.add_subplot(gs[1:3, 0])
    matrice_np = np.array(matrice)
    
    # Display the input matrix (using a distinct colormap for clarity)
    ax_input.imshow(matrice_np, cmap='Pastel1', vmin=0, vmax=COLORS)
    ax_input.set_title("Input Grid", fontweight='bold')
    ax_input.axis('off')
    
    # Add text numbers inside the cells for exact context
    for y in range(HEIGHT):
        for x in range(WIDTH):
            val = matrice_np[y, x]
            text = str(val) if val != 0 else "."
            ax_input.text(x, y, text, ha="center", va="center", color="black", fontweight='bold')

    # --- B. Plotting the Feature Maps ---
    # Find the global maximum activation value to normalize the colors
    vmax = np.max(feature_maps)
    
    for i in range(32):
        row = i // 8
        col = (i % 8) + 1  # Add 1 to skip the first column (reserved for input)
        
        ax = fig.add_subplot(gs[row, col])
        fmap = feature_maps[i]
        
        # Display with a heatmap (colormap 'magma')
        im = ax.imshow(fmap, cmap='magma', vmin=0, vmax=vmax)
        ax.set_title(f"Filter {i}")
        ax.axis('off') # Hide X and Y axes for clarity
        
    # Add a colorbar legend for the activation levels
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    fig.colorbar(im, cax=cbar_ax, label="Activation level (Signal)")
    
    # Adjust layout to fit everything nicely without overlapping
    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.show()

if __name__ == "__main__":
    main()
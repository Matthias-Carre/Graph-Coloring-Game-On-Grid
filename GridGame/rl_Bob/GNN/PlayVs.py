import torch
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import environment and model
from ColoringEnvGNN import GraphColoringEnv
from ModelGNN import GraphColoringNet
from game.Grid import Grid

def decode_action(action, width, num_colors):
    """Decodes the action index into x, y, and color."""
    c = (action % num_colors) + 1
    cell_idx = action // num_colors
    x = cell_idx % width
    y = cell_idx // width
    return x, y, c

def build_grid_edges(width, height):
    """Creates the static edge index for the grid topology."""
    edges = []
    for y in range(height):
        for x in range(width):
            node = y * width + x
            if x > 0: edges.append([node, node - 1])
            if x < width - 1: edges.append([node, node + 1])
            if y > 0: edges.append([node, node - width])
            if y < height - 1: edges.append([node, node + width])
    return torch.tensor(edges, dtype=torch.long).t().contiguous()

def main():
    # Configuration matching train.py
    WIDTH = 12
    HEIGHT = 12
    COLORS = 4 
    
    # Adjust path according to your folder structure
    MODEL_PATH = "rl_Bob/GNN/latest.pt"  
    
    device = torch.device("cpu")

    # Initialize the Graph Transformer model
    model = GraphColoringNet(
        width=WIDTH, 
        height=HEIGHT, 
        num_colors=COLORS, 
        hidden_dim=128, 
        num_layers=3
    )
    
    try:
        checkpoint = torch.load(MODEL_PATH, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval() 
        print("Model loaded successfully.")
    except FileNotFoundError:
        print(f"Error: The file {MODEL_PATH} was not found.")
        return

    # Initialize the static edge index
    edge_index = build_grid_edges(WIDTH, HEIGHT).to(device)

    # Board initialization
    env = GraphColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    env.reset() 
    
    # Override grid to clear the internal AI's opening move
    env.grid = Grid(HEIGHT, WIDTH, COLORS)
    
    print("\n========================================")
    print("  MATCH: YOU (ALICE) VS AI (BOB)  ")
    print("========================================")

    def check_victory():
        """Checks win conditions for both players."""
        if env.has_uncolorable_cell():
            print("\nBOB WINS: A dead node was created.")
            return True
        if env.is_grid_full():
            print("\nALICE WINS: The grid is full and no dead nodes exist.")
            return True
        return False

    done = False
    
    while not done:
        env.render() 
        
        # Human turn (Alice)
        valid_move = False
        while not valid_move:
            try:
                print("\nYour turn (Alice)!")
                x = int(input(f"Choose X (0 to {WIDTH-1}): "))
                y = int(input(f"Choose Y (0 to {HEIGHT-1}): "))
                c = int(input(f"Choose Color (1 to {COLORS}): "))
                
                # Check move validity
                if env.grid.is_move_valid(x, y, c) and env.grid.get_cell(x, y).get_value() == 0:
                    env.grid.player = 0
                    env.grid.play_move(x, y, c)
                    valid_move = True
                else:
                    print("Illegal move. Respect rules and choose an empty cell.")
            except ValueError:
                print("Please enter valid integers.")
            except IndexError:
                print("Coordinates out of bounds.")

        if check_victory():
            break

        env.render()
        
        # AI turn (Bob)
        print("\nAI is thinking...")
        obs_dict = env._get_obs()

        # Transform to tensor and add batch dimension
        obs_tensor = torch.tensor(obs_dict["observation"], dtype=torch.float32).unsqueeze(0).to(device)
        mask_tensor = torch.tensor(obs_dict["mask"], dtype=torch.bool).unsqueeze(0).to(device)

        with torch.no_grad():
            # Pass both observation and edge index
            logits, _ = model(obs_tensor, edge_index)
            
            # Apply action masking
            logits = logits.masked_fill(~mask_tensor, -1e8)

            # Select best action
            best_action = torch.argmax(logits, dim=1).item()

        # Decode and apply move
        b_x, b_y, b_c = decode_action(best_action, WIDTH, COLORS)
        print(f"AI plays: X={b_x}, Y={b_y} with Color={b_c}")

        env.grid.player = 1
        env.grid.play_move(b_x, b_y, b_c)

        if check_victory():
            break
            
        # Fallback if no moves remain
        if not np.any(env._get_obs()["mask"]):
            print("\nGame over. No legal moves left.")
            break

    env.render()
    print("END OF MATCH.")

if __name__ == "__main__":
    main()
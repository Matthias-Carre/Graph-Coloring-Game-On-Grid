import torch
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import environment and model
from ColoringEnv import GraphColoringEnv
from Model import GraphColoringNet

def decode_action(action, width, num_colors):
    """
    Decode action index using the same mapping as GraphColoringEnv:
    action = (y * width + x) * num_colors + (color - 1)
    """
    c = (action % num_colors) + 1
    cell_idx = action // num_colors
    x = cell_idx % width
    y = cell_idx // width
    return x, y, c

def build_grid_edges(width, height):
    """
    Create the static edge index for the grid topology.
    """
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
    # Configuration
    WIDTH, HEIGHT, COLORS = 7, 7, 4 
    
    # Adjust path according to your folder structure
    MODEL_PATH = "rl_Alice/latest.pt"  
    
    device = torch.device("cpu")

    # Initialize the Graph Transformer model
    model = GraphColoringNet(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    
    try:
        checkpoint = torch.load(MODEL_PATH, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval() 
        print("Brain loaded successfully!")
    except FileNotFoundError:
        print(f"Error: The file {MODEL_PATH} was not found.")
        return

    # Initialize the static edge index for the Graph Transformer
    edge_index = build_grid_edges(WIDTH, HEIGHT).to(device)

    # Board initialization
    env = GraphColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    env.reset() 
    
    print("\n" + "="*40)
    print("  MATCH OF THE CENTURY: YOU vs ALICE  ")
    print("="*40)

    def stop_if_bob_wins():
        """
        Stop the game when at least one empty cell has no legal color.
        """
        if env.has_uncolorable_cell():
            print("\nBOB WINS: at least one vertex has no legal color left.")
            return True
        return False

    done = False
    start = True
    
    while not done:
        env.render() 

        # Alice turn (AI)
        obs_dict = env._get_obs()

        # Transform for PyTorch and add batch dimension
        obs_tensor = torch.tensor(obs_dict["observation"], dtype=torch.float32).unsqueeze(0).to(device)
        mask_tensor = torch.tensor(obs_dict["mask"], dtype=torch.bool).unsqueeze(0).to(device)

        # Alice makes a greedy decision (no exploration)
        with torch.no_grad():
            # Pass both the observation and the edge index to the Graph Transformer
            logits, _ = model(obs_tensor, edge_index)

            # Apply Action Masking
            logits = logits.masked_fill(~mask_tensor, -1e8)

            # Pick the action with the highest confidence
            best_action = torch.argmax(logits, dim=1).item()

        # Translate integer to playable move
        a_x, a_y, a_c = decode_action(best_action, WIDTH, COLORS)
        print(f"Alice plays: X={a_x}, Y={a_y} with Color={a_c} (Action n°{best_action})")

        # Apply Alice's move to the grid
        env.grid.player = 0
        
        if start:
            start = False
            
        env.grid.play_move(a_x, a_y, a_c)

        if stop_if_bob_wins():
            break

        env.render()
        
        # Check if the board is full after Alice's turn
        if env.is_grid_full() or not np.any(env._get_obs()["mask"]):
            print("\nThe game is over!")
            break
        
        # Human turn (You)
        valid_move = False
        while not valid_move:
            try:
                print("\nIt is your turn!")
                x = int(input(f"Choose X (0 to {WIDTH-1}): "))
                y = int(input(f"Choose Y (0 to {HEIGHT-1}): "))
                c = int(input(f"Choose Color (1 to {COLORS}): "))
                
                # Check validity of the human move
                if env.grid.is_move_valid(x, y, c) and env.grid.get_cell(x, y).get_value() == 0:
                    env.grid.player = 1
                    env.grid.play_move(x, y, c)

                    if stop_if_bob_wins():
                        done = True
                        break

                    valid_move = True
                else:
                    print("Illegal move! Respect neighborhood rules or choose an empty cell.")
            except ValueError:
                print("Please enter valid integers.")
            except IndexError:
                print("Coordinates are out of bounds.")

        # End if no playable move remains
        if env.is_grid_full() or not np.any(env._get_obs()["mask"]):
            print("\nThe game is over!")
            break

    env.render()
    print("END OF MATCH!")

if __name__ == "__main__":
    main()
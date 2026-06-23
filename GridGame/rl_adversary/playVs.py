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

def main():
    # --- 1. CONFIGURATION ---
    # Use the same dimensions as the last training session
    WIDTH, HEIGHT, COLORS = 4, 4, 4 
    #MODEL_PATH = "GridGame/NN/4x4.pt"
    script_dir = Path(__file__).parent.parent
    MODEL_PATH = str(script_dir / "checkpoints" / "latest.pt")

    # --- 2. WAKING UP ALICE ---
    model = GraphColoringNet(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    
    try:
        checkpoint = torch.load(MODEL_PATH, map_location="cpu")
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval() # Freeze the network in evaluation mode
        print("Brain loaded successfully!")
    except FileNotFoundError:
        print(f"Error: The file {MODEL_PATH} was not found.")
        return

    # --- 3. BOARD INITIALIZATION ---
    env = GraphColoringEnv(width=WIDTH, height=HEIGHT, num_colors=COLORS)
    env.reset() # Initialize empty grid
    
    print("\n" + "="*40)
    print("  MATCH OF THE CENTURY: YOU vs ALICE  ")
    print("="*40)

    def stop_if_bob_wins():
        """Stops the game when at least one empty cell has no legal color."""
        if env.has_uncolorable_cell():
            print("\nBOB WINS: at least one vertex has no legal color left.")
            return True
        return False

    done = False
    
    while not done:
        env.render() # Display current grid state

        # ==========================================
        #             ALICE TURN (AI)
        # ==========================================

        # 1. Retrieve current grid vision
        obs_dict = env._get_obs()

        # 2. Transform for PyTorch
        obs_tensor = torch.tensor(obs_dict["observation"], dtype=torch.float32).unsqueeze(0)
        mask_tensor = torch.tensor(obs_dict["mask"], dtype=torch.bool).unsqueeze(0)

        # 3. Alice makes a greedy decision (no exploration)
        with torch.no_grad():
            logits, _ = model(obs_tensor)

            # Apply Action Masking
            logits = logits.masked_fill(~mask_tensor, -1e8)

            # Alice picks the action with the highest confidence
            best_action = torch.argmax(logits, dim=1).item()

        # 4. Translate integer to playable move
        a_x, a_y, a_c = decode_action(best_action, WIDTH, COLORS)
        print(f"Alice plays: X={a_x}, Y={a_y} with Color={a_c} (Action n°{best_action})")

        # 5. Apply Alice's move to the grid
        env.grid.player = 0
        env.grid.play_move(a_x, a_y, a_c)

        if stop_if_bob_wins():
            break

        env.render()
        # Check if the board is full after Alice's turn
        if env.is_grid_full() or not np.any(env._get_obs()["mask"]):
            print("\nThe game is over!")
            break
        
        # ==========================================
        #           HUMAN TURN (YOU)
        # ==========================================
        valid_move = False
        while not valid_move:
            try:
                print("\nIt is your turn!")
                x = int(input(f"Choose X (0 to {WIDTH-1}): "))
                y = int(input(f"Choose Y (0 to {HEIGHT-1}): "))
                c = int(input(f"Choose Color (1 to {COLORS}): "))
                
                # Security check using your grid methods
                # Modify "env.grid.is_move_valid" if your method has a different name
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

        # End if no playable move remains for Alice.
        if env.is_grid_full() or not np.any(env._get_obs()["mask"]):
            print("\nThe game is over!")
            break

    env.render()
    print("END OF MATCH! (Check who won based on your scoring rules)")

if __name__ == "__main__":
    main()
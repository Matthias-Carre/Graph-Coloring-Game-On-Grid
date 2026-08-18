"""
Stats script: run Bob's GNN model against Alice (random or heuristic) over many games
and report win rates, similar to randomVsRandom.py.

Usage:
    python statsModel.py --w 4 --h 4 --colors 4 --games 500 --alice random
    python statsModel.py --w 4 --h 4 --colors 4 --games 500 --alice heuristic
    python statsModel.py --w 8 --h 8 --colors 4 --games 500 --alice all
"""

import torch
import numpy as np
import argparse
import sys
from pathlib import Path

# Add project root to path so game.* imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ColoringEnvGNN import GraphColoringEnv
from ModelGNN import GraphColoringNet
from game.Grid import Grid
from game.Alice.alice import Alice
from game.Bob.bob import Bob


# ---------------------------------------------------------------------------
# Helpers shared with randomVsRandom.py
# ---------------------------------------------------------------------------

def is_grid_full(grid):
    for j in range(grid.height):
        for i in range(grid.width):
            if grid.get_cell(i, j).get_value() == 0:
                return False
    return True


def has_uncolorable_cell(grid):
    for j in range(grid.height):
        for i in range(grid.width):
            if grid.get_cell(i, j).is_uncolorable:
                return True
    return False


def build_grid_edges(width, height):
    """Static edge index for the grid graph."""
    edges = []
    for y in range(height):
        for x in range(width):
            node = y * width + x
            if x > 0:               edges.append([node, node - 1])
            if x < width - 1:       edges.append([node, node + 1])
            if y > 0:               edges.append([node, node - width])
            if y < height - 1:      edges.append([node, node + width])
    return torch.tensor(edges, dtype=torch.long).t().contiguous()


def decode_action(action, width, num_colors):
    c = (action % num_colors) + 1
    cell_idx = action // num_colors
    x = cell_idx % width
    y = cell_idx // width
    return x, y, c


def get_obs(grid, width, height, num_colors):
    """Build the node-feature observation matching ColoringEnvGNN._get_obs."""
    num_nodes = width * height
    obs = np.zeros((num_nodes, num_colors + 1), dtype=np.float32)
    for j in range(height):
        for i in range(width):
            val = grid.get_cell(i, j).get_value()
            node_idx = j * width + i
            obs[node_idx, val] = 1.0
    return obs


def action_masks(grid, width, height, num_colors):
    """Valid-action mask matching ColoringEnvGNN.action_masks."""
    total = width * height * num_colors
    mask = np.zeros(total, dtype=bool)
    for j in range(height):
        for i in range(width):
            cell = grid.get_cell(i, j)
            if cell.get_value() != 0 or cell.is_uncolorable:
                continue
            for c in range(1, num_colors + 1):
                if grid.is_move_valid(i, j, c):
                    idx = (j * width + i) * num_colors + (c - 1)
                    mask[idx] = True
    return mask


# ---------------------------------------------------------------------------
# Core match loop
# ---------------------------------------------------------------------------

def run_model_vs_alice(width, height, num_colors, num_games, alice_mode, model, edge_index, device):
    """
    Bob = GNN model, Alice = random or heuristic.
    Returns a dict of statistics.
    """
    assert alice_mode in ("random", "heuristic"), f"Unknown alice_mode: {alice_mode}"

    alice_wins = 0
    bob_wins = 0
    alice_kills_herself = 0
    bob_kills_alice = 0
    colored_proportions = []

    for i in range(num_games):
        grid = Grid(height, width, num_colors)
        alice = Alice(grid)
        while True:
            # ---- Alice's turn ------------------------------------------------
            grid.player = 0

            if alice_mode == "random":
                alice_move = alice.next_random_move()
            else:
                alice_move = alice.next_heuristic1_move()

            if alice_move is None:
                # No move available for Alice → Bob wins by default
                bob_wins += 1
                #print("Alice has no valid moves. Bob wins by default.")
                break

            x, y, col = alice_move
            grid.play_move(x, y, col)

            if is_grid_full(grid):
                alice_wins += 1
                #print("Grid is full. Alice wins!")
                break
            if has_uncolorable_cell(grid):
                bob_wins += 1
                #print("Alice created a dead node. Bob wins!")
                alice_kills_herself += 1
                break

            # ---- Bob's turn (GNN model) ---------------------------------------
            grid.player = 1

            obs = get_obs(grid, width, height, num_colors)
            mask = action_masks(grid, width, height, num_colors)

            if not np.any(mask):
                # No valid move for Bob
                alice_wins += 1
                #print("Bob has no valid moves. Alice wins by default.")
                break

            obs_tensor = torch.tensor(obs, dtype=torch.float32).unsqueeze(0).to(device)
            mask_tensor = torch.tensor(mask, dtype=torch.bool).unsqueeze(0).to(device)

            """ version with the best action
            with torch.no_grad():
                logits, _ = model(obs_tensor, edge_index)
                logits = logits.masked_fill(~mask_tensor, -1e8)
                best_action = torch.argmax(logits, dim=1).item()
            """
            
            # version with sampling from the distribution
            with torch.no_grad():
                logits, _ = model(obs_tensor, edge_index)
                # Mask illegal moves by setting their logits to a very small number
                logits = logits.masked_fill(~mask_tensor, -1e8)
                # Create a categorical distribution from the masked logits
                dist = torch.distributions.Categorical(logits=logits)
                # Sample an action based on the probability distribution
                best_action = dist.sample().item()



            bx, by, bc = decode_action(best_action, width, num_colors)
            grid.play_move(bx, by, bc)

            if is_grid_full(grid):
                alice_wins += 1
                #print("Grid is full. Alice wins!")
                break
            if has_uncolorable_cell(grid):
                bob_wins += 1
                bob_kills_alice += 1
                #print("Bob created a dead node. Bob wins!")
                break

        colored_proportions.append(grid.proportion_colored_cells())
        
    #render(grid)
    avg_prop = sum(colored_proportions) / len(colored_proportions)
    return {
        "alice_wins": alice_wins,
        "bob_wins": bob_wins,
        "alice_kills_herself": alice_kills_herself,
        "bob_kills_alice": bob_kills_alice,
        "avg_colored_proportion": avg_prop,
    }


def print_stats(stats, num_games, width, height, num_colors, alice_mode, model_path):
    print(f"\n[Model: {model_path}]  Alice mode: {alice_mode.upper()}")
    print(f"Grid {width}x{height}, {num_colors} colors, {num_games} games")
    aw = stats["alice_wins"]
    bw = stats["bob_wins"]
    print(f"  Alice wins:           {aw:5d}  ({100*aw/num_games:5.1f}%)")
    print(f"  Bob   wins:           {bw:5d}  ({100*bw/num_games:5.1f}%)")
    print(f"  Alice kills herself:  {stats['alice_kills_herself']:5d}  ({100*stats['alice_kills_herself']/num_games:5.1f}%)")
    print(f"  Bob kills Alice:      {stats['bob_kills_alice']:5d}  ({100*stats['bob_kills_alice']/num_games:5.1f}%)")
    print(f"  Avg colored cells:    {stats['avg_colored_proportion']:.3f}")
    print("-" * 50)


def render(grid):
    """Displays current grid state in terminal."""
    print(f"\n===  ===")
        
    player_color = {
        0: "\033[91m",
        1: "\033[94m",
    }
    reset = "\033[0m"
        
    first_row = ""
    for i in range(grid.width):
        first_row += f"{i} "
    print(f"  {first_row}")

    for j in range(grid.height):
        row_str = f"{j} "
        for i in range(grid.width):
            cell = grid.get_cell(i, j)
            val = cell.get_value()

            if val == 0:
                row_str += ". "
                continue

            color = player_color.get(cell.played_by, "")
            row_str += f"{color}{val}{reset} "
        print(row_str)
    print("===================")



# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Evaluate Bob's GNN model win-rate vs Alice.")
    parser.add_argument("--w",      type=int,   default=4,              help="Grid width.")
    parser.add_argument("--h",      type=int,   default=4,              help="Grid height.")
    parser.add_argument("--colors", type=int,   default=4,              help="Number of colors.")
    parser.add_argument("--games",  type=int,   default=500,            help="Games per configuration.")
    parser.add_argument("--alice",  type=str,   default="all",
                        choices=["random", "heuristic", "all"],         help="Alice's strategy.")
    parser.add_argument("--model",  type=str,   default="latest.pt",    help="Path to Bob's checkpoint (.pt).")
    parser.add_argument("--hidden", type=int,   default=128,            help="Model hidden dim.")
    parser.add_argument("--layers", type=int,   default=3,              help="Model num layers.")
    parser.add_argument("--sweep",  action="store_true",
                        help="Run a sweep over multiple grid sizes (like randomVsRandom).")
    args = parser.parse_args()

    device = torch.device("cpu")

    # Resolve model path (relative to this script's directory if not absolute)
    model_path = Path(args.model)
    if not model_path.is_absolute():
        model_path = Path(__file__).parent / model_path

    # Load model
    model = GraphColoringNet(
        width=args.w,
        height=args.h,
        num_colors=args.colors,
        hidden_dim=args.hidden,
        num_layers=args.layers,
    )
    try:
        checkpoint = torch.load(str(model_path), map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        print(f"Model loaded from {model_path}")
    except FileNotFoundError:
        print(f"Error: checkpoint not found at {model_path}")
        return

    alice_modes = ["random", "heuristic"] if args.alice == "all" else [args.alice]

    alice_modes = ["heuristic"]
    
    if args.sweep:
        sizes = [11,12,13,14,15,16,17,18,19,20]
        for size in sizes:
            edge_index = build_grid_edges(size, size).to(device)
            # Reload model with the right width/height
            m = GraphColoringNet(
                width=size, height=size,
                num_colors=args.colors,
                hidden_dim=args.hidden,
                num_layers=args.layers,
            )
            try:
                m.load_state_dict(checkpoint["model_state_dict"])
                m.eval()
            except Exception:
                print(f"  Skipping {size}x{size}: model incompatible.")
                continue
            for mode in alice_modes:
                stats = run_model_vs_alice(size, size, args.colors, args.games, mode, m, edge_index, device)
                print_stats(stats, args.games, size, size, args.colors, mode, model_path)
    else:
        edge_index = build_grid_edges(args.w, args.h).to(device)
        for mode in alice_modes:
            stats = run_model_vs_alice(args.w, args.h, args.colors, args.games, mode, model, edge_index, device)
            print_stats(stats, args.games, args.w, args.h, args.colors, mode, model_path)


if __name__ == "__main__":
    main()

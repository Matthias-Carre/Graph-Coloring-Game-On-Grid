import argparse
from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd


def load_metrics(csv_path: Path) -> tuple[pd.DataFrame, str]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {csv_path}")

    # Read first line to parse metadata
    with csv_path.open("r", encoding="utf-8") as f:
        first_line = f.readline().strip()

    title = None
    # Example: "Alice Training On size: w=7, h=7, c=4"
    m = re.match(r"^(?P<player>\w+)\s+Training\s+On\s+size:\s*w=(?P<w>\d+),\s*h=(?P<h>\d+),\s*c=(?P<c>\d+)", first_line)
    if m:
        player = m.group("player")
        w = m.group("w")
        h = m.group("h")
        c = m.group("c")
        title = f"{player} grid {w}x{h}, c={c}"
    else:
        title = first_line  # Fallback to raw first line if parsing fails

    # Ignore the first line of the CSV
    df = pd.read_csv(csv_path, skiprows=1)
    if "batch" not in df.columns:
        raise ValueError("CSV file must contain a 'batch' column")

    df = df.sort_values("batch").reset_index(drop=True)
    return df, title


def plot_all_on_single_page(df: pd.DataFrame, cols: int = 3, title: str | None = None, save_path: Path | None = None) -> None:
    """Plot all relevant metrics on a single window using subplots."""
    metrics = [
        ("win_rate", "Win rate"),
        ("max_score", "Max score"),
        ("avg_score", "Average score"),
        ("min_score", "Min score"),
        ("avg_length", "Average episode length"),
        ("actor_loss", "Actor loss"),
        ("value_loss", "Value loss"),
        ("entropy_loss", "Entropy loss"),
    ]

    n_plots = len(metrics) + 1
    rows = (n_plots + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 3.5 * rows))
    axes = axes.flatten()

    for idx, (col_name, title_) in enumerate(metrics):
        ax = axes[idx]
        if col_name not in df.columns:
            ax.text(0.5, 0.5, f"{col_name} not found", ha="center")
            ax.set_title(title_)
            ax.set_xticks([])
            ax.set_yticks([])
            continue

        ax.plot(df["batch"], df[col_name], marker="o", linewidth=1.2)
        ax.set_title(title_)
        ax.set_xlabel("Batch")
        ax.grid(True, alpha=0.3)

    # Plot avg_length and win_rate on twin axes
    comb_idx = len(metrics)
    if comb_idx < len(axes):
        ax_comb = axes[comb_idx]
        
        # Target columns
        length_col = "avg_length"
        win_col = "win_rate"

        if length_col in df.columns and win_col in df.columns:
            ax_length = ax_comb
            ax_win = ax_length.twinx()
            
            # Plot average length on the primary y-axis
            ax_length.plot(df["batch"], df[length_col], color="tab:blue", marker="o", linewidth=1.5)
            
            # Plot win rate on the secondary y-axis
            ax_win.plot(df["batch"], df[win_col], color="tab:orange", marker="s", linewidth=1.5)
            
            # Set titles and labels
            ax_length.set_title("Average Length and Win Rate vs Batch")
            ax_length.set_xlabel("Batch")
            ax_length.set_ylabel("Average Episode Length")
            
            ax_win.set_ylabel("Win Rate")
            ax_win.set_ylim(0, 1)
            
            # Enable grid for the primary axis
            ax_length.grid(True, alpha=0.3)
        else:
            ax_comb.text(0.5, 0.5, "No length or win_rate found", ha="center")
            ax_comb.set_title("Comparison")

    # Hide any unused axes
    for j in range(n_plots, len(axes)):
        axes[j].axis("off")

    # Set a global title if provided
    if title:
        fig.suptitle(title, fontsize=14)
        fig.tight_layout(rect=[0, 0, 1, 0.96])
    else:
        fig.tight_layout()

    # Save the figure or show it on screen
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Plot successfully saved to: {save_path}")
    else:
        plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot training metrics vs batch (single-window).")
    parser.add_argument(
        "--csv-path",
        type=str,
        default=str(Path(__file__).parent / "checkpoints" / "Alice" / "training_metrics.csv"),
        help="Path to the metrics CSV file.",
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=3,
        help="Number of columns in the subplot grid.",
    )
    
    # Require exactly 2 arguments for the save option: path and name
    parser.add_argument(
        "--save",
        nargs=2,
        metavar=("PATH", "NAME"),
        help="Save the plot to the specified path and filename instead of displaying it.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    df, title = load_metrics(csv_path)

    print(f"Loaded {len(df)} rows from {csv_path}")
    
    # Construct the full save path if the argument was passed
    save_file = None
    if args.save:
        save_file = Path(args.save[0]) / args.save[1]

    plot_all_on_single_page(df, cols=args.cols, title=title, save_path=save_file)


if __name__ == "__main__":
    main()
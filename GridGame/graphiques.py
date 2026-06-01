import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def load_metrics(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if "batch" not in df.columns:
        raise ValueError("CSV file must contain a 'batch' column")

    df = df.sort_values("batch").reset_index(drop=True)
    return df


def plot_all_on_single_page(df: pd.DataFrame, cols: int = 3) -> None:
    """Plot all relevant metrics on a single window using subplots.

    The function looks for standard columns and skips missing ones.
    """
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

    # Add combined score vs win_rate as an extra subplot
    n_plots = len(metrics) + 1
    rows = (n_plots + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 3.5 * rows))
    axes = axes.flatten()

    for idx, (col_name, title) in enumerate(metrics):
        ax = axes[idx]
        if col_name not in df.columns:
            ax.text(0.5, 0.5, f"{col_name} not found", ha="center")
            ax.set_title(title)
            ax.set_xticks([])
            ax.set_yticks([])
            continue

        ax.plot(df["batch"], df[col_name], marker="o", linewidth=1.2)
        ax.set_title(title)
        ax.set_xlabel("Batch")
        ax.grid(True, alpha=0.3)

    # Combined score vs win_rate
    comb_idx = len(metrics)
    if comb_idx < len(axes):
        ax_comb = axes[comb_idx]
        score_column = None
        for candidate in ("max_score", "avg_score"):
            if candidate in df.columns:
                score_column = candidate
                break

        if score_column is not None and "win_rate" in df.columns:
            ax_score = ax_comb
            ax_win = ax_score.twinx()
            ax_score.plot(df["batch"], df[score_column], color="tab:blue", marker="o", linewidth=1.5)
            ax_win.plot(df["batch"], df["win_rate"], color="tab:orange", marker="s", linewidth=1.5)
            ax_score.set_title(f"{score_column} and win rate vs batch")
            ax_score.set_xlabel("Batch")
            ax_score.set_ylabel(score_column)
            ax_win.set_ylabel("Win rate")
            ax_win.set_ylim(0, 1)
            ax_score.grid(True, alpha=0.3)
        else:
            ax_comb.text(0.5, 0.5, "No score or win_rate found", ha="center")
            ax_comb.set_title("Comparison")

    # Hide any unused axes
    for j in range(n_plots, len(axes)):
        axes[j].axis("off")

    fig.tight_layout()
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
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    df = load_metrics(csv_path)

    print(f"Loaded {len(df)} rows from {csv_path}")
    plot_all_on_single_page(df, cols=args.cols)


if __name__ == "__main__":
    main()

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


def plot_metric(df: pd.DataFrame, column: str, title: str, ylabel: str) -> None:
    if column not in df.columns:
        print(f"Skipping {column}: column not found")
        return

    plt.figure(figsize=(10, 5))
    plt.plot(df["batch"], df[column], marker="o", linewidth=1.8)
    plt.title(title)
    plt.xlabel("Batch")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def plot_metrics(df: pd.DataFrame) -> None:
    plots = [
        ("win_rate", "Win rate vs batch", "Win rate"),
        ("max_score", "Max score vs batch", "Max score"),
        ("avg_score", "Average score vs batch", "Average score"),
        ("min_score", "Min score vs batch", "Min score"),
        ("avg_length", "Average episode length vs batch", "Average episode length"),
        ("actor_loss", "Actor loss vs batch", "Actor loss"),
        ("value_loss", "Value loss vs batch", "Value loss"),
        ("entropy_loss", "Entropy loss vs batch", "Entropy loss"),
    ]

    for column, title, ylabel in plots:
        plot_metric(df, column, title, ylabel)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot training metrics vs batch.")
    parser.add_argument(
        "--csv-path",
        type=str,
        default=str(Path(__file__).parent / "checkpoints" / "Alice" / "training_metrics.csv"),
        help="Path to the metrics CSV file.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    df = load_metrics(csv_path)

    print(f"Loaded {len(df)} rows from {csv_path}")
    plot_metrics(df)


if __name__ == "__main__":
    main()

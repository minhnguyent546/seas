import json

import matplotlib.pyplot as plt
import scienceplots  # noqa: F401

# Use science plots style for professional appearance
plt.style.use(["science", "ieee"])


def load_evaluation_data(file_path):
    """Load evaluation results from JSON file"""
    with open(file_path, "r") as f:
        data = json.load(f)
    return data


def create_retrieval_metrics_chart(data, output_path=None):
    """Create a professional chart showing retrieval metrics performance"""

    # Set up the figure with high DPI for publication quality
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    # Define colors for each metric (colorblind-friendly palette)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
    markers = ["o", "s", "^", "D"]

    # Extract k values from the data (now all metrics have correct k values)
    k_values = [1, 3, 5, 10]

    for i, metric_data in enumerate(data):
        metric_name = metric_data["metric"]
        results = metric_data["results"]

        # Extract k values and corresponding metric values
        k_vals = [r["k"] for r in results]
        values = [r["value"] for r in results]

        # Plot the metric
        ax.plot(
            k_vals,
            values,
            marker=markers[i],
            color=colors[i],
            linewidth=2,
            markersize=8,
            label=metric_name,
            markerfacecolor="white",
            markeredgewidth=2,
            markeredgecolor=colors[i],
        )

    # Customize the plot
    ax.set_xlabel("k (Number of Retrieved Documents)", fontsize=12)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title(
        "Evaluation results for the Retrieval", fontsize=14, fontweight="bold"
    )

    # Set x-axis ticks
    ax.set_xticks(k_values)
    ax.set_xticklabels([f"@{k}" for k in k_values])

    # Set y-axis limits with some padding
    all_values = []
    for metric_data in data:
        all_values.extend([r["value"] for r in metric_data["results"]])

    y_min = min(all_values) - 0.02
    y_max = max(all_values) + 0.02
    ax.set_ylim(y_min, y_max)

    # Add grid for better readability
    ax.grid(True, alpha=0.3, linestyle="--")

    # Add legend
    ax.legend(loc="lower right", frameon=True, fancybox=True, shadow=True)

    # Tight layout to prevent label cutoff
    plt.tight_layout()

    # Save the plot if output path is provided
    if output_path:
        plt.savefig(
            output_path,
            dpi=300,
            bbox_inches="tight",
            facecolor="white",
            edgecolor="none",
        )
        print(f"Chart saved to: {output_path}")

    # Show the plot
    plt.show()

    return fig, ax


def create_metric_comparison_table(data):
    """Create a summary table of the metrics"""
    print("\n" + "=" * 60)
    print("Evaluation results for the Retrieval")
    print("=" * 60)
    print(f"{'Metric':<8} {'@1':<8} {'@3':<8} {'@5':<8} {'@10':<8}")
    print("-" * 60)

    for metric_data in data:
        metric_name = metric_data["metric"]
        results = metric_data["results"]

        # Extract values directly since all metrics now have correct k values
        values = [r["value"] for r in results]

        # Pad with the last value if we don't have enough data points
        while len(values) < 4:
            values.append(values[-1])

        print(
            f"{metric_name:<8} {values[0]:<8.4f} {values[1]:<8.4f} {values[2]:<8.4f} {values[3]:<8.4f}"
        )

    print("=" * 60)


def main():
    """Main function to create the visualization"""
    # File paths
    data_file = "/home/minhnguyent546/Documents/WIP/seas/api/all_evaluation_results_for_chart.json"
    output_file = "/home/minhnguyent546/Documents/WIP/seas/api/retrieval_metrics_chart.png"

    try:
        # Load the data
        print("Loading evaluation data...")
        data = load_evaluation_data(data_file)

        # Create summary table
        create_metric_comparison_table(data)

        # Create the chart
        print("\nCreating professional chart...")
        create_retrieval_metrics_chart(data, output_file)

        print("\nVisualization complete!")

    except FileNotFoundError:
        print(f"Error: Could not find the data file at {data_file}")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in the data file")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()

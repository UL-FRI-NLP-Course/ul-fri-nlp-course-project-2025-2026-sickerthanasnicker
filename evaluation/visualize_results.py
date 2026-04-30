import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from io_utils import load_jsonl


DEFAULT_JUDGEMENTS_FILE = Path(__file__).with_name("results") / "judgements.jsonl"
DEFAULT_RETRIEVAL_FILE = Path(__file__).with_name("results") / "retrieval.jsonl"
DEFAULT_OUTPUT_DIR = Path(__file__).with_name("results")

METRICS = ["correctness", "grounding", "completeness", "clarity", "hallucination"]


def grouped_judgement_summary(rows):
    groups = defaultdict(list)
    for row in rows:
        key = (row.get("model_id") or row.get("model") or "model", row["variant"])
        groups[key].append(row)

    summary = []
    for (model_id, variant), items in sorted(groups.items()):
        item = {
            "model_id": model_id,
            "model_label": items[0].get("display_name") or model_id,
            "variant": variant,
            "n": len(items),
        }
        for metric in METRICS:
            item[metric] = sum(float(row[metric]) for row in items) / len(items)
        unanswerable = [row for row in items if row["type"] == "unanswerable"]
        item["refusal_accuracy"] = (
            sum(1 for row in unanswerable if row["refusal"]) / len(unanswerable)
            if unanswerable
            else 0.0
        )
        summary.append(item)
    return summary


def retrieval_summary(rows):
    answerable = [row for row in rows if row["type"] != "unanswerable"]
    unanswerable = [row for row in rows if row["type"] == "unanswerable"]
    hit_rate = (
        sum(1 for row in answerable if row["hit"]) / len(answerable)
        if answerable
        else 0.0
    )
    false_evidence = (
        sum(1 for row in unanswerable if row["reference_keyword_fraction"] >= 0.35) / len(unanswerable)
        if unanswerable
        else 0.0
    )
    avg_context = (
        sum(float(row["context_length_words"]) for row in rows) / len(rows)
        if rows
        else 0.0
    )
    return {
        "answerable_hit_rate": hit_rate,
        "unanswerable_false_evidence_rate": false_evidence,
        "average_context_length_words": avg_context,
    }


def labels(summary):
    return [f"{row.get('model_label', row['model_id'])}\n{row['variant']}" for row in summary]


def save_summary_scores(summary, output_dir):
    score_metrics = ["correctness", "grounding", "completeness", "clarity"]
    x_labels = labels(summary)
    x = range(len(summary))
    width = 0.18

    fig, ax = plt.subplots(figsize=(max(10, len(summary) * 1.3), 6))
    for i, metric in enumerate(score_metrics):
        offsets = [value + (i - 1.5) * width for value in x]
        ax.bar(offsets, [row[metric] for row in summary], width, label=metric)

    ax.set_ylim(0, 5)
    ax.set_ylabel("Average score (0-5)")
    ax.set_title("Answer Quality by Model and Variant")
    ax.set_xticks(list(x))
    ax.set_xticklabels(x_labels, rotation=35, ha="right")
    ax.legend()
    fig.tight_layout()
    save_figure(fig, output_dir / "summary_scores")
    plt.close(fig)


def save_hallucination(summary, output_dir):
    fig, ax = plt.subplots(figsize=(max(9, len(summary) * 1.2), 5))
    ax.bar(labels(summary), [row["hallucination"] for row in summary], color="#b94a48")
    ax.set_ylim(0, 5)
    ax.set_ylabel("Average hallucination score (0-5, lower is better)")
    ax.set_title("Hallucination by Model and Variant")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    save_figure(fig, output_dir / "hallucination_by_model")
    plt.close(fig)


def save_refusal(summary, output_dir):
    fig, ax = plt.subplots(figsize=(max(9, len(summary) * 1.2), 5))
    ax.bar(labels(summary), [row["refusal_accuracy"] for row in summary], color="#4f81bd")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Refusal accuracy on unanswerable questions")
    ax.set_title("Refusal Accuracy")
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    save_figure(fig, output_dir / "refusal_accuracy")
    plt.close(fig)


def save_retrieval(summary, output_dir):
    fig, ax = plt.subplots(figsize=(7, 5))
    names = ["answerable hit rate", "false evidence rate"]
    values = [
        summary["answerable_hit_rate"],
        summary["unanswerable_false_evidence_rate"],
    ]
    ax.bar(names, values, color=["#4f81bd", "#b94a48"])
    ax.set_ylim(0, 1)
    ax.set_title("Retrieval Quality")
    ax.set_ylabel("Rate")
    ax.text(
        0.5,
        -0.22,
        f"Average context length: {summary['average_context_length_words']:.1f} words",
        transform=ax.transAxes,
        ha="center",
    )
    fig.tight_layout()
    save_figure(fig, output_dir / "retrieval_quality")
    plt.close(fig)


def save_figure(fig, path_without_suffix):
    fig.savefig(path_without_suffix.with_suffix(".png"), dpi=160, facecolor="white")
    fig.savefig(path_without_suffix.with_suffix(".jpg"), dpi=160, facecolor="white")
    fig.savefig(path_without_suffix.with_suffix(".svg"), facecolor="white")


def save_csv(summary, retrieval, output_dir):
    columns = [
        "model_id",
        "model_label",
        "variant",
        "n",
        "correctness",
        "grounding",
        "completeness",
        "clarity",
        "hallucination",
        "refusal_accuracy",
    ]
    with open(output_dir / "summary_scores.csv", "w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        for row in summary:
            writer.writerow({column: row[column] for column in columns})

    with open(output_dir / "retrieval_summary.csv", "w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(retrieval.keys()))
        writer.writeheader()
        writer.writerow(retrieval)


def markdown_table(rows, columns):
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, sep]
    for row in rows:
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                value = f"{value:.2f}"
            values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def save_report(summary, retrieval, output_dir):
    columns = [
        "model_id",
        "model_label",
        "variant",
        "n",
        "correctness",
        "grounding",
        "completeness",
        "clarity",
        "hallucination",
        "refusal_accuracy",
    ]
    content = f"""# Evaluation Results

## Answer Scores

{markdown_table(summary, columns)}

## Retrieval

- Answerable hit rate: {retrieval['answerable_hit_rate']:.3f}
- Unanswerable false evidence rate: {retrieval['unanswerable_false_evidence_rate']:.3f}
- Average context length: {retrieval['average_context_length_words']:.1f} words

## Charts

![Summary scores](summary_scores.png)

SVG: [summary_scores.svg](summary_scores.svg)
JPG: [summary_scores.jpg](summary_scores.jpg)

![Hallucination by model](hallucination_by_model.png)

SVG: [hallucination_by_model.svg](hallucination_by_model.svg)
JPG: [hallucination_by_model.jpg](hallucination_by_model.jpg)

![Refusal accuracy](refusal_accuracy.png)

SVG: [refusal_accuracy.svg](refusal_accuracy.svg)
JPG: [refusal_accuracy.jpg](refusal_accuracy.jpg)

![Retrieval quality](retrieval_quality.png)

SVG: [retrieval_quality.svg](retrieval_quality.svg)
JPG: [retrieval_quality.jpg](retrieval_quality.jpg)

CSV tables:

- [summary_scores.csv](summary_scores.csv)
- [retrieval_summary.csv](retrieval_summary.csv)
"""
    (output_dir / "report.md").write_text(content, encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Visualize evaluation results.")
    parser.add_argument("--judgements", type=Path, default=DEFAULT_JUDGEMENTS_FILE)
    parser.add_argument("--retrieval", type=Path, default=DEFAULT_RETRIEVAL_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    judgements = load_jsonl(args.judgements)
    retrieval_rows = load_jsonl(args.retrieval)

    answer_summary = grouped_judgement_summary(judgements)
    retrieval = retrieval_summary(retrieval_rows)

    save_summary_scores(answer_summary, args.output_dir)
    save_hallucination(answer_summary, args.output_dir)
    save_refusal(answer_summary, args.output_dir)
    save_retrieval(retrieval, args.output_dir)
    save_csv(answer_summary, retrieval, args.output_dir)
    save_report(answer_summary, retrieval, args.output_dir)

    print(f"Saved charts and report to {args.output_dir}")


if __name__ == "__main__":
    main()

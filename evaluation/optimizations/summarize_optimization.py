import argparse
import csv
from collections import defaultdict
from pathlib import Path

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ModuleNotFoundError:
    HAS_MATPLOTLIB = False
    plt = None

from common import EVALUATION_DIR

from io_utils import load_jsonl


DEFAULT_JUDGEMENTS = EVALUATION_DIR / "results" / "optimization" / "judgements.jsonl"
DEFAULT_RETRIEVAL = EVALUATION_DIR / "results" / "optimization" / "retrieval.jsonl"
DEFAULT_OUTPUT_DIR = EVALUATION_DIR / "results" / "optimization"

METRICS = ["correctness", "grounding", "completeness", "clarity", "hallucination"]


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


def group_summary(rows):
    groups = defaultdict(list)
    for row in rows:
        key = (
            row.get("model_id", ""),
            row.get("variant", ""),
            row.get("prompt_id", "unknown_prompt"),
            row.get("settings_id", "unknown_settings"),
        )
        groups[key].append(row)

    summary = []
    for (model_id, variant, prompt_id, settings_id), items in sorted(groups.items()):
        record = {
            "model_id": model_id,
            "model_label": items[0].get("display_name", model_id),
            "variant": variant,
            "prompt_id": prompt_id,
            "settings_id": settings_id,
            "n": len(items),
        }
        for metric in METRICS:
            record[metric] = sum(float(item[metric]) for item in items) / len(items)
        unanswerable = [item for item in items if item.get("type") == "unanswerable"]
        record["refusal_accuracy"] = (
            sum(1 for item in unanswerable if item.get("refusal")) / len(unanswerable)
            if unanswerable
            else 0.0
        )
        summary.append(record)
    return summary


def label(row):
    return f"{row['model_label']}\n{row['variant']}\n{row['prompt_id']}\n{row['settings_id']}"


def save_figure(fig, path_without_suffix):
    fig.savefig(path_without_suffix.with_suffix(".png"), dpi=160, facecolor="white")
    fig.savefig(path_without_suffix.with_suffix(".jpg"), dpi=160, facecolor="white")
    fig.savefig(path_without_suffix.with_suffix(".svg"), facecolor="white")


def save_bar(summary, metric, output_dir, filename, title, ylabel, color):
    fig, ax = plt.subplots(figsize=(max(12, len(summary) * 1.0), 6))
    ax.bar([label(row) for row in summary], [row[metric] for row in summary], color=color)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 5 if metric != "refusal_accuracy" else 1)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    save_figure(fig, output_dir / filename)
    plt.close(fig)


def write_summary_csv(summary, output_dir):
    columns = [
        "model_id",
        "model_label",
        "variant",
        "prompt_id",
        "settings_id",
        "n",
        "correctness",
        "grounding",
        "completeness",
        "clarity",
        "hallucination",
        "refusal_accuracy",
    ]
    with open(output_dir / "optimization_summary.csv", "w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in summary:
            writer.writerow({column: row[column] for column in columns})


def write_retrieval_csv(retrieval, output_dir):
    with open(output_dir / "optimization_retrieval_summary.csv", "w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(retrieval.keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerow(retrieval)


def chart_section():
    if not HAS_MATPLOTLIB:
        return "Charts were skipped because `matplotlib` is not installed in this environment.\n"
    return """![Correctness](optimization_correctness.png)

![Hallucination](optimization_hallucination.png)

![Refusal accuracy](optimization_refusal_accuracy.png)
"""


def write_report(summary, retrieval, output_dir):
    columns = [
        "model_id",
        "variant",
        "prompt_id",
        "settings_id",
        "n",
        "correctness",
        "grounding",
        "completeness",
        "clarity",
        "hallucination",
        "refusal_accuracy",
    ]
    ranked = sorted(
        [row for row in summary if row["variant"] == "rag"],
        key=lambda row: (-row["correctness"], row["hallucination"], -row["grounding"]),
    )
    best = ranked[:5]
    content = f"""# Correctness Optimization Results

These results are separate from the main reproducible evaluation. They compare system prompts and generation settings for model optimization.

## Best RAG Configurations

{markdown_table(best, columns) if best else "No RAG rows found."}

## Full Summary

{markdown_table(summary, columns)}

## Retrieval

- Answerable hit rate: {retrieval['answerable_hit_rate']:.3f}
- Unanswerable false evidence rate: {retrieval['unanswerable_false_evidence_rate']:.3f}
- Average context length: {retrieval['average_context_length_words']:.1f} words

## Charts

{chart_section()}

CSV tables:

- [optimization_summary.csv](optimization_summary.csv)
- [optimization_retrieval_summary.csv](optimization_retrieval_summary.csv)
"""
    (output_dir / "optimization_report.md").write_text(content, encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Summarize correctness optimization judgements.")
    parser.add_argument("--judgements", type=Path, default=DEFAULT_JUDGEMENTS)
    parser.add_argument("--retrieval", type=Path, default=DEFAULT_RETRIEVAL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    judgements = load_jsonl(args.judgements)
    retrieval_rows = load_jsonl(args.retrieval)
    summary = group_summary(judgements)
    retrieval = retrieval_summary(retrieval_rows)

    if HAS_MATPLOTLIB:
        save_bar(summary, "correctness", args.output_dir, "optimization_correctness", "Optimization Correctness", "Average correctness (0-5)", "#4f81bd")
        save_bar(summary, "hallucination", args.output_dir, "optimization_hallucination", "Optimization Hallucination", "Average hallucination (0-5, lower is better)", "#b94a48")
        save_bar(summary, "refusal_accuracy", args.output_dir, "optimization_refusal_accuracy", "Optimization Refusal Accuracy", "Refusal accuracy", "#5f9b5f")
    else:
        print("matplotlib is not installed; skipping optimization charts.")
    write_summary_csv(summary, args.output_dir)
    write_retrieval_csv(retrieval, args.output_dir)
    write_report(summary, retrieval, args.output_dir)

    print(f"Saved optimization summary to {args.output_dir}")


if __name__ == "__main__":
    main()

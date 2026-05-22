import argparse
from pathlib import Path

from evaluation.eval_config import EVALUATION_DIR
from evaluation.io_utils import load_jsonl, write_jsonl
from evaluation.progress_utils import Progress
from evaluation.retrieval_shared import (
    CHUNKS_FILE,
    build_index,
    format_context,
    load_chunks,
    retrieve,
    source_label,
)
from evaluation.text_utils import content_terms


DEFAULT_QUESTIONS_FILE = EVALUATION_DIR / "questions.jsonl"
DEFAULT_OUTPUT_FILE = EVALUATION_DIR / "results" / "retrieval.jsonl"


def keyword_hit(reference, context, threshold):
    keywords = set(content_terms(reference))
    if not keywords:
        return False, 0.0, []

    context_terms = set(content_terms(context))
    matches = sorted(keywords & context_terms)
    fraction = len(matches) / len(keywords)
    return fraction >= threshold, fraction, matches


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--chunks", type=Path, default=CHUNKS_FILE)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.35)
    parser.add_argument("--quiet", action="store_true", help="Disable per-question progress output.")
    return parser.parse_args()


def main():
    args = parse_args()
    questions = load_jsonl(args.questions)
    chunks = load_chunks(args.chunks)
    index = build_index(chunks)

    rows = []
    answerable_hits = []
    unanswerable_false_hits = []
    context_lengths = []

    progress = Progress(len(questions), "retrieval_eval") if not args.quiet else None
    for idx, item in enumerate(questions, start=1):
        results = retrieve(item["question"], index, chunks, args.top_k)
        context = format_context(results)
        context_lengths.append(len(context.split()))
        hit, fraction, matches = keyword_hit(item["reference"], context, args.threshold)

        if item["type"] == "unanswerable":
            unanswerable_false_hits.append(hit)
            metric_hit = None
        else:
            answerable_hits.append(hit)
            metric_hit = hit

        rows.append(
            {
                "id": item["id"],
                "type": item["type"],
                "question": item["question"],
                "top_k": args.top_k,
                "hit": metric_hit,
                "reference_keyword_fraction": round(fraction, 3),
                "matched_keywords": matches,
                "context_length_words": len(context.split()),
                "corpus_path": str(args.chunks),
                "top_sources": [
                    {"source": source_label(chunk), "score": float(score)}
                    for chunk, score in results
                ],
            }
        )
        if progress:
            progress.log(idx, f"question={item['id']}")

    write_jsonl(args.output, rows)

    hit_rate = sum(answerable_hits) / len(answerable_hits) if answerable_hits else 0.0
    false_hit_rate = (
        sum(unanswerable_false_hits) / len(unanswerable_false_hits)
        if unanswerable_false_hits
        else 0.0
    )
    avg_context_length = sum(context_lengths) / len(context_lengths) if context_lengths else 0.0

    print("Retrieval evaluation")
    print(f"questions: {len(questions)} | top_k: {args.top_k} | chunks: {args.chunks} | output: {args.output}")
    print(f"answerable hit rate: {hit_rate:.3f}")
    print(f"unanswerable false evidence rate: {false_hit_rate:.3f}")
    print(f"average context length: {avg_context_length:.1f} words")


if __name__ == "__main__":
    main()

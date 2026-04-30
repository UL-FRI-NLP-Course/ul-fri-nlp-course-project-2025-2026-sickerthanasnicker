import argparse
import sys
from pathlib import Path


EVALUATION_DIR = Path(__file__).resolve().parents[1]
if str(EVALUATION_DIR) not in sys.path:
    sys.path.insert(0, str(EVALUATION_DIR))

from io_utils import load_jsonl, write_jsonl
from progress_utils import Progress
from retrieval_shared import build_index, format_context, load_chunks, retrieve


DEFAULT_QUESTIONS_FILE = EVALUATION_DIR / "questions.jsonl"
DEFAULT_OUTPUT_DIR = EVALUATION_DIR / "fine_tuning" / "data"

SYSTEM_PROMPT = (
    "Si slovenski asistent za delovno pravo. Odgovarjaj samo na podlagi "
    "podanega konteksta. Če kontekst ne vsebuje odgovora, to jasno povej."
)


def ideal_answer(item):
    if item["type"] == "unanswerable":
        return "Iz podanega konteksta ni mogoče zanesljivo odgovoriti."
    return f"Na podlagi podanega konteksta: {item['reference']}"


def make_example(item, context):
    user = f"Kontekst:\n{context}\n\nVprašanje: {item['question']}"
    return {
        "id": item["id"],
        "type": item["type"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": ideal_answer(item)},
        ],
        "metadata": {
            "source": "evaluation/questions.jsonl",
            "task": "grounded_slovenian_employment_law_qa",
        },
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare grounded QA JSONL for later fine-tuning.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_FILE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--corpus-chunks",
        type=Path,
        default=None,
        help="Optional normalized chunk JSONL to reuse for retrieval contexts.",
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--dev-every", type=int, default=5)
    parser.add_argument("--quiet", action="store_true", help="Disable data-prep progress output.")
    return parser.parse_args()


def main():
    args = parse_args()
    questions = load_jsonl(args.questions)
    chunks = load_chunks(args.corpus_chunks) if args.corpus_chunks else load_chunks()
    index = build_index(chunks)

    train = []
    dev = []
    progress = Progress(len(questions), "fine_tuning_examples") if not args.quiet else None
    for idx, item in enumerate(questions, start=1):
        results = retrieve(item["question"], index, chunks, args.top_k)
        example = make_example(item, format_context(results))
        if idx % args.dev_every == 0:
            dev.append(example)
        else:
            train.append(example)
        if progress:
            progress.log(idx, f"question={item['id']}")

    write_jsonl(args.output_dir / "train.jsonl", train)
    write_jsonl(args.output_dir / "dev.jsonl", dev)

    readme = """# Fine-Tuning Data

This folder contains grounded QA examples prepared from the evaluation set.
It is intentionally a preparation step only: it does not run expensive PEFT,
LoRA, or Ollama model creation by default.

Each row uses chat-style JSONL:

- system: domain and grounding rules;
- user: retrieved context plus question;
- assistant: ideal grounded answer or refusal.

Possible next steps:

- use these rows as a tiny sanity dataset for LoRA/PEFT experiments;
- expand with more COLESLAW-derived employment-law QA pairs;
- create an Ollama Modelfile that bakes in the system prompt;
- evaluate any tuned model with `python evaluation/run_eval.py --arena`.
"""
    (args.output_dir / "README.md").write_text(readme, encoding="utf-8")

    chunk_source = args.corpus_chunks if args.corpus_chunks else "report/code/data/chunk.jsonl"
    print(f"Saved {len(train)} train and {len(dev)} dev examples to {args.output_dir}")
    print(f"Retrieval chunks: {chunk_source}")


if __name__ == "__main__":
    main()

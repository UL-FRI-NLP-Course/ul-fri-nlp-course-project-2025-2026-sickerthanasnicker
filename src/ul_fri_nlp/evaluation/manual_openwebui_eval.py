import argparse
import json
import time
from pathlib import Path

from ul_fri_nlp.evaluation.eval_config import EVALUATION_DIR, load_env
from ul_fri_nlp.evaluation.io_utils import load_jsonl
from ul_fri_nlp.evaluation.model_providers import chat_openwebui
from ul_fri_nlp.evaluation.retrieval_shared import build_index, format_context, load_chunks, retrieve


DEFAULT_OUTPUT = EVALUATION_DIR / "results" / "manual_openwebui_eval_answers.jsonl"
DEFAULT_QUESTIONS = EVALUATION_DIR / "questions.jsonl"


def parse_args():
    parser = argparse.ArgumentParser(description="Run manual-review answer collection for the final Open WebUI model.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", default="ul-fri-slovenian-employment-law-rag-openwebui")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-tokens", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main():
    load_env()
    args = parse_args()
    questions = load_jsonl(args.questions)
    if args.limit is not None:
        questions = questions[: args.limit]

    chunks = load_chunks()
    index = build_index(chunks)
    options = {
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_tokens": args.max_tokens,
        "seed": args.seed,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as fp:
        for idx, item in enumerate(questions, start=1):
            results = retrieve(item["question"], index, chunks, top_k=args.top_k)
            context = format_context(results)
            messages = [
                {
                    "role": "user",
                    "content": f"Kontekst:\n{context}\n\nVprašanje: {item['question']}",
                }
            ]
            started = time.time()
            try:
                answer = chat_openwebui(args.model, messages, options)
                error = ""
            except Exception as exc:
                answer = ""
                error = f"{type(exc).__name__}: {exc}"

            row = {
                "id": item["id"],
                "type": item["type"],
                "question": item["question"],
                "reference": item["reference"],
                "model": args.model,
                "provider": "openwebui",
                "top_k": args.top_k,
                "context": context,
                "answer": answer,
                "error": error,
                "elapsed_seconds": round(time.time() - started, 3),
                "settings": options,
            }
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[{idx}/{len(questions)}] {item['id']} {error or 'ok'}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

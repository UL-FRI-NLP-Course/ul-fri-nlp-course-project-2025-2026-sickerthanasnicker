import argparse
from pathlib import Path

from common import EVALUATION_DIR, load_optimization_config, load_questions, prompt_by_id, resolve_optimization_path

from io_utils import write_jsonl
from retrieval_shared import build_index, format_context, load_chunks, retrieve
from text_utils import split_sentences


DEFAULT_TRAIN = resolve_optimization_path("data/peft_train.jsonl")
DEFAULT_DEV = resolve_optimization_path("data/peft_dev.jsonl")
TARGET_MODEL = "mistral-7b"


def ideal_answer(item):
    if item["type"] == "unanswerable":
        return "Iz podanega konteksta ni mogoče zanesljivo odgovoriti."
    return f"Na podlagi podanega konteksta: {item['reference']}"


def qa_example(item, context, system_prompt):
    return {
        "id": f"eval-{item['id']}",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Kontekst:\n{context}\n\nVprašanje: {item['question']}"},
            {"role": "assistant", "content": ideal_answer(item)},
        ],
        "metadata": {
            "example_source": "evaluation_questions",
            "question_type": item["type"],
            "target_model": TARGET_MODEL,
        },
    }


def summarize_chunk(text, max_words):
    sentences = split_sentences(text)
    summary = " ".join(sentences[:2]) if sentences else text
    words = summary.split()
    if len(words) > max_words:
        summary = " ".join(words[:max_words]).rstrip(",.;") + "."
    return f"Na podlagi podanega konteksta: {summary}"


def corpus_example(chunk, idx, system_prompt, max_answer_words):
    title = chunk.get("meta", {}).get("title") or chunk.get("meta", {}).get("law") or "vir"
    return {
        "id": f"corpus-{idx:05d}",
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Kontekst:\n"
                    f"{chunk['text']}\n\n"
                    "Vprašanje: Katero pravno pravilo ali informacijo iz delovnega prava vsebuje ta kontekst?"
                ),
            },
            {"role": "assistant", "content": summarize_chunk(chunk["text"], max_answer_words)},
        ],
        "metadata": {
            "example_source": "coleslaw_employment_chunk",
            "source_title": title,
            "source_id": chunk.get("id", ""),
            "target_model": TARGET_MODEL,
        },
    }


def split_train_dev(rows, dev_every):
    train = []
    dev = []
    for idx, row in enumerate(rows, start=1):
        if dev_every and idx % dev_every == 0:
            dev.append(row)
        else:
            train.append(row)
    return train, dev


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare PEFT-ready grounded chat data from optimized corpus chunks.")
    parser.add_argument("--config", type=Path, default=Path(__file__).with_name("config.json"))
    parser.add_argument("--questions", type=Path, default=EVALUATION_DIR / "questions.jsonl")
    parser.add_argument("--corpus-chunks", type=Path, default=None)
    parser.add_argument("--train-output", type=Path, default=DEFAULT_TRAIN)
    parser.add_argument("--dev-output", type=Path, default=DEFAULT_DEV)
    parser.add_argument("--prompt-id", default="strict_grounded_v1")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--dev-every", type=int, default=5)
    parser.add_argument("--max-corpus-examples", type=int, default=80)
    parser.add_argument("--max-answer-words", type=int, default=90)
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_optimization_config(args.config)
    prompt = prompt_by_id(config, args.prompt_id)
    corpus_path = args.corpus_chunks or resolve_optimization_path(config["retrieval"]["corpus_chunks"])
    if not corpus_path.exists():
        raise FileNotFoundError(
            f"Optimized corpus chunks not found: {corpus_path}. "
            "Run evaluation/optimizations/prepare_corpus.py first."
        )

    top_k = args.top_k or int(config["retrieval"].get("top_k", 3))
    chunks = load_chunks(corpus_path)
    index = build_index(chunks)
    questions = load_questions(args.questions)
    examples = []

    for item in questions:
        results = retrieve(item["question"], index, chunks, top_k)
        examples.append(qa_example(item, format_context(results), prompt["system"]))

    for idx, chunk in enumerate(chunks[: args.max_corpus_examples], start=1):
        examples.append(corpus_example(chunk, idx, prompt["system"], args.max_answer_words))

    train, dev = split_train_dev(examples, args.dev_every)
    write_jsonl(args.train_output, train)
    write_jsonl(args.dev_output, dev)

    print(f"Saved {len(train)} train and {len(dev)} dev PEFT examples.")
    print(f"Target model: {TARGET_MODEL}")
    print(f"Train: {args.train_output}")
    print(f"Dev: {args.dev_output}")


if __name__ == "__main__":
    main()

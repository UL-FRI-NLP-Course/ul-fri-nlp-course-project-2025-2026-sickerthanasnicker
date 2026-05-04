import argparse
from pathlib import Path

from common import EVALUATION_DIR, load_optimization_config, load_questions, prompt_by_id, resolve_optimization_path

from io_utils import write_jsonl
from progress_utils import Progress
from retrieval_shared import build_index, format_context, load_chunks, retrieve
from text_utils import content_terms, split_sentences


DEFAULT_TRAIN = resolve_optimization_path("data/peft_train.jsonl")
DEFAULT_DEV = resolve_optimization_path("data/peft_dev.jsonl")
TARGET_MODEL = "mistral-7b"

LEGAL_SUMMARY_TERMS = [
    "zakon o delovnih razmerjih",
    "zdr",
    "pogodba o zaposlitvi",
    "odpoved pogodbe",
    "odpovedni rok",
    "izredna odpoved",
    "redna odpoved",
    "letni dopust",
    "delodajalec",
    "delavec",
    "delovno razmerje",
    "plača",
    "odpravnina",
    "poskusno delo",
    "delovni čas",
]


def reference_supported(reference, context, threshold=0.35):
    reference_terms = set(content_terms(reference))
    if not reference_terms:
        return False
    context_terms = set(content_terms(context))
    return len(reference_terms & context_terms) / len(reference_terms) >= threshold


def ideal_answer(item, context):
    if item["type"] == "unanswerable":
        return "Iz podanega konteksta ni mogoče zanesljivo odgovoriti."
    if not reference_supported(item["reference"], context):
        return "Iz podanega konteksta ni mogoče zanesljivo odgovoriti."
    return f"Na podlagi podanega konteksta: {item['reference']}"


def qa_example(item, context, system_prompt):
    return {
        "id": f"eval-{item['id']}",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Kontekst:\n{context}\n\nVprašanje: {item['question']}"},
            {"role": "assistant", "content": ideal_answer(item, context)},
        ],
        "metadata": {
            "example_source": "evaluation_questions",
            "question_type": item["type"],
            "target_model": TARGET_MODEL,
        },
    }


def summarize_chunk(text, max_words):
    sentences = split_sentences(text)
    if sentences:
        scored = []
        for idx, sentence in enumerate(sentences):
            lowered = sentence.lower()
            score = sum(1 for term in LEGAL_SUMMARY_TERMS if term in lowered)
            score += min(3, len(content_terms(sentence)) // 10)
            scored.append((score, -idx, sentence))
        scored.sort(reverse=True)
        selected = [sentence for score, _idx, sentence in scored[:2] if score > 0]
        summary = " ".join(selected) if selected else sentences[0]
    else:
        summary = text
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
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--quiet", action="store_true", help="Disable data-prep progress output.")
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

    question_progress = Progress(len(questions), "peft_question_examples") if not args.quiet else None
    for idx, item in enumerate(questions, start=1):
        results = retrieve(item["question"], index, chunks, top_k)
        examples.append(qa_example(item, format_context(results), prompt["system"]))
        if question_progress:
            question_progress.log(idx, f"question={item['id']}")

    selected_chunks = chunks[: args.max_corpus_examples]
    corpus_progress = Progress(len(selected_chunks), "peft_corpus_examples", every=args.progress_every) if not args.quiet else None
    for idx, chunk in enumerate(selected_chunks, start=1):
        examples.append(corpus_example(chunk, idx, prompt["system"], args.max_answer_words))
        if corpus_progress:
            corpus_progress.log(idx, f"chunk={chunk.get('id', idx)}")

    train, dev = split_train_dev(examples, args.dev_every)
    write_jsonl(args.train_output, train)
    write_jsonl(args.dev_output, dev)

    print(f"Saved {len(train)} train and {len(dev)} dev PEFT examples.")
    print(f"Target model: {TARGET_MODEL}")
    print(f"Train: {args.train_output}")
    print(f"Dev: {args.dev_output}")


if __name__ == "__main__":
    main()

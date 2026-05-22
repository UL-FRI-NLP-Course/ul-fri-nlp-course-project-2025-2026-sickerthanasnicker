import argparse
from pathlib import Path

from ul_fri_nlp.optimizations.common import (
    EVALUATION_DIR,
    OPTIMIZATION_DIR,
    enabled_items,
    load_optimization_config,
    load_questions,
    resolve_optimization_path,
    select_items,
)

from ul_fri_nlp.evaluation.eval_config import load_env
from ul_fri_nlp.evaluation.io_utils import append_jsonl, write_jsonl
from ul_fri_nlp.evaluation.model_providers import chat_model
from ul_fri_nlp.evaluation.progress_utils import Progress
from ul_fri_nlp.evaluation.retrieval_eval import keyword_hit
from ul_fri_nlp.evaluation.retrieval_shared import CHUNKS_FILE, build_index, format_context, load_chunks, retrieve, source_label
from ul_fri_nlp.evaluation.run_eval import offline_answer


DEFAULT_OUTPUT = EVALUATION_DIR / "results" / "optimization" / "prompt_sweep_answers.jsonl"
DEFAULT_RETRIEVAL_OUTPUT = EVALUATION_DIR / "results" / "optimization" / "retrieval.jsonl"

BASELINE_USER_TEMPLATE = (
    "Odgovori na vprašanje iz slovenskega prava. Če nisi prepričan, to jasno povej.\n\n"
    "Vprašanje: {question}"
)

RAG_USER_TEMPLATE = (
    "Odgovori IZKLJUČNO na podlagi podanega konteksta. "
    "Če odgovor ni v kontekstu, povej, da ni mogoče zanesljivo odgovoriti.\n\n"
    "Kontekst:\n{context}\n\n"
    "Vprašanje: {question}"
)


def build_messages(system_prompt, question, context, variant):
    if variant == "baseline":
        user = BASELINE_USER_TEMPLATE.format(question=question)
    else:
        user = RAG_USER_TEMPLATE.format(question=question, context=context)
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user},
    ]


def load_retrieval_corpus(config, args):
    configured = resolve_optimization_path(config["retrieval"]["corpus_chunks"])
    corpus_path = args.corpus_chunks or configured
    if corpus_path.exists():
        return load_chunks(corpus_path), corpus_path, "optimization_corpus"
    return load_chunks(CHUNKS_FILE), CHUNKS_FILE, "project_rag_chunks"


def call_model(model_config, messages, options, question, variant, context, results):
    provider = model_config["provider"]
    model = model_config["model"]
    if provider == "offline":
        return offline_answer(question, variant, context, results), "offline", ""
    try:
        return chat_model(provider, model, messages, options), provider, ""
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        return f"[ERROR: model call failed: {error}]", f"{provider}_error", error


def make_answer_row(item, variant, context, answer, model_config, prompt, settings, provider_used, error, corpus_path, top_k):
    return {
        "id": item["id"],
        "variant": variant,
        "question": item["question"],
        "context": context,
        "answer": answer,
        "model_id": model_config["model_id"],
        "display_name": model_config.get("display_name", model_config["model_id"]),
        "provider": provider_used,
        "model": model_config["model"],
        "prompt_mode": "no_context" if variant == "baseline" else "rag_context",
        "prompt_id": prompt["prompt_id"],
        "prompt_label": prompt.get("label", prompt["prompt_id"]),
        "system_prompt": prompt["system"],
        "settings_id": settings["settings_id"],
        "temperature": settings["temperature"],
        "top_p": settings["top_p"],
        "max_tokens": settings["max_tokens"],
        "seed": settings["seed"],
        "top_k": top_k,
        "corpus_path": str(corpus_path),
        "error": error,
    }


def make_retrieval_row(item, results, context, top_k, threshold, corpus_path):
    hit, fraction, matches = keyword_hit(item["reference"], context, threshold)
    metric_hit = None if item["type"] == "unanswerable" else hit
    return {
        "id": item["id"],
        "type": item["type"],
        "question": item["question"],
        "top_k": top_k,
        "hit": metric_hit,
        "reference_keyword_fraction": round(fraction, 3),
        "matched_keywords": matches,
        "context_length_words": len(context.split()),
        "corpus_path": str(corpus_path),
        "top_sources": [
            {"source": source_label(chunk), "score": float(score)}
            for chunk, score in results
        ],
    }


def selected_models(config, args):
    models = select_items(config["models"], "model_id", args.model_id)
    if args.provider is None:
        return models
    overridden = []
    for model in models:
        item = dict(model)
        item["provider"] = args.provider
        if args.provider == "offline":
            item["model"] = "offline"
            item["model_id"] = f"offline-{model['model_id']}"
            item["display_name"] = f"offline {model.get('display_name', model['model_id'])}"
        overridden.append(item)
    return overridden


def parse_args():
    load_env()
    parser = argparse.ArgumentParser(description="Run correctness optimization prompt/config sweeps.")
    parser.add_argument("--config", type=Path, default=OPTIMIZATION_DIR / "config.json")
    parser.add_argument("--questions", type=Path, default=EVALUATION_DIR / "questions.jsonl")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--retrieval-output", type=Path, default=DEFAULT_RETRIEVAL_OUTPUT)
    parser.add_argument("--corpus-chunks", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--threshold", type=float, default=0.35)
    parser.add_argument("--model-id", action="append", help="Limit to a configured model_id. Repeatable.")
    parser.add_argument("--prompt-id", action="append", help="Limit to a configured prompt_id. Repeatable.")
    parser.add_argument("--settings-id", action="append", help="Limit to a configured settings_id. Repeatable.")
    parser.add_argument(
        "--provider",
        choices=["offline", "ollama", "openwebui", "openai"],
        default=None,
        help="Override provider for selected configured models; use offline for smoke tests.",
    )
    parser.add_argument("--quiet", action="store_true", help="Disable per-step progress output.")
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_optimization_config(args.config)
    questions = load_questions(args.questions, args.limit)
    top_k = args.top_k or int(config["retrieval"].get("top_k", 3))
    models = selected_models(config, args)
    prompts = select_items(config["prompts"], "prompt_id", args.prompt_id)
    settings_list = select_items(config["generation_settings"], "settings_id", args.settings_id)

    chunks, corpus_path, corpus_source = load_retrieval_corpus(config, args)
    index = build_index(chunks)
    retrieved = {}
    retrieval_rows = []
    retrieval_progress = Progress(len(questions), "optimization_retrieval") if not args.quiet else None
    for idx, item in enumerate(questions, start=1):
        results = retrieve(item["question"], index, chunks, top_k)
        context = format_context(results)
        retrieved[item["id"]] = (results, context)
        retrieval_rows.append(make_retrieval_row(item, results, context, top_k, args.threshold, corpus_path))
        if retrieval_progress:
            retrieval_progress.log(idx, f"question={item['id']}")

    write_jsonl(args.retrieval_output, retrieval_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("", encoding="utf-8")

    row_count = 0
    total_calls = len(models) * len(prompts) * len(settings_list) * len(questions) * 2
    progress = Progress(total_calls, "optimization_generation") if not args.quiet else None
    for model_index, model_config in enumerate(models, start=1):
        if not args.quiet:
            print(
                f"[optimization_model] {model_index}/{len(models)} "
                f"{model_config['model_id']} ({model_config['provider']} / {model_config['model']})",
                flush=True,
            )
        for prompt_index, prompt in enumerate(prompts, start=1):
            if not args.quiet:
                print(f"[optimization_prompt] {prompt_index}/{len(prompts)} {prompt['prompt_id']}", flush=True)
            for settings_index, settings in enumerate(settings_list, start=1):
                if not args.quiet:
                    print(
                        f"[optimization_settings] {settings_index}/{len(settings_list)} "
                        f"{settings['settings_id']} temp={settings['temperature']} top_p={settings['top_p']}",
                        flush=True,
                    )
                for question_index, item in enumerate(questions, start=1):
                    results, context = retrieved[item["id"]]
                    for variant in ("baseline", "rag"):
                        active_context = "" if variant == "baseline" else context
                        active_results = [] if variant == "baseline" else results
                        messages = build_messages(prompt["system"], item["question"], active_context, variant)
                        answer, provider_used, error = call_model(
                            model_config,
                            messages,
                            settings,
                            item["question"],
                            variant,
                            active_context,
                            active_results,
                        )
                        row = make_answer_row(
                            item,
                            variant,
                            active_context,
                            answer,
                            model_config,
                            prompt,
                            settings,
                            provider_used,
                            error,
                            corpus_path,
                            top_k,
                        )
                        append_jsonl(args.output, row)
                        row_count += 1
                        if progress:
                            progress.log(
                                row_count,
                                (
                                    f"model={model_config['model_id']} prompt={prompt['prompt_id']} "
                                    f"settings={settings['settings_id']} question={question_index}/{len(questions)} "
                                    f"id={item['id']} variant={variant}"
                                ),
                            )

    print(f"Saved {row_count} optimization answers to {args.output}")
    print(f"Saved {len(retrieval_rows)} retrieval rows to {args.retrieval_output}")
    print(f"Questions: {len(questions)} | models: {len(models)} | prompts: {len(prompts)} | settings: {len(settings_list)}")
    print(f"Retrieval corpus: {corpus_source} ({corpus_path})")


if __name__ == "__main__":
    main()

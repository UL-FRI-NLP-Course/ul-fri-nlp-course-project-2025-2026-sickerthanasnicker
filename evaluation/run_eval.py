import argparse
from pathlib import Path

from eval_config import (
    enabled_arena_models,
    generation_options,
    get_default_model,
    get_default_provider,
    load_config,
    load_env,
)
from io_utils import append_jsonl, load_jsonl
from model_providers import chat_model
from progress_utils import Progress
from retrieval_shared import build_index, format_context, load_chunks, retrieve, source_label
from text_utils import content_terms, split_sentences


DEFAULT_QUESTIONS_FILE = Path(__file__).with_name("questions.jsonl")
DEFAULT_OUTPUT_FILE = Path(__file__).with_name("results") / "answers.jsonl"

BASELINE_PROMPT = (
    "Odgovori na vprašanje iz slovenskega prava. "
    "Če nisi prepričan, to jasno povej."
)

RAG_PROMPT = (
    "Odgovori IZKLJUČNO na podlagi podanega konteksta. "
    "Če odgovor ni v kontekstu, povej, da ni mogoče zanesljivo odgovoriti."
)

ANSWER_SOURCE_PRIORITY = {
    "primary_law": 3,
    "official_interpretation": 2,
    "official_operational_guidance": 1,
    "official_case_law": 0,
}

CASE_LAW_QUESTION_TERMS = ("sodna praksa", "sodni praksi", "sodišče", "sodišča", "judikat")


def should_refuse_from_context(question, context, results):
    if not context.strip() or not results:
        return True

    top_score = float(results[0][1])
    if top_score <= 0:
        return True

    question_terms = set(content_terms(question))
    context_terms = set(content_terms(context))
    overlap = question_terms & context_terms
    if len(overlap) < min(2, len(question_terms)):
        return True

    required_terms = {
        "avstrij", "ddv", "deduj", "dedn", "elektronsk", "gospodarsk",
        "knjig", "omejen", "registrsk", "stanovanj", "starš", "ustanov",
    }
    return bool((question_terms & required_terms) - context_terms)


def extractive_answer(question, results):
    question_terms = set(content_terms(question))
    asks_case_law = any(term in (question or "").lower() for term in CASE_LAW_QUESTION_TERMS)
    candidates = []

    for source_rank, (chunk, _score) in enumerate(results):
        label = source_label(chunk)
        source_type = chunk.get("meta", {}).get("source_type", "")
        if asks_case_law:
            source_priority = 4 if source_type == "official_case_law" else ANSWER_SOURCE_PRIORITY.get(source_type, 0)
        else:
            source_priority = ANSWER_SOURCE_PRIORITY.get(source_type, 0)
        for sentence in split_sentences(chunk["text"]):
            sentence_terms = set(content_terms(sentence))
            overlap = len(question_terms & sentence_terms)
            if overlap:
                candidates.append((overlap, source_priority, -source_rank, label, sentence))

    if not candidates:
        return "Iz podanega konteksta ni mogoče zanesljivo odgovoriti."

    candidates.sort(key=lambda item: (item[1], item[0], item[2]), reverse=True)
    selected = []
    seen = set()
    label_counts = {}
    for _overlap, _source_priority, _rank, label, sentence in candidates:
        key = (label, sentence)
        if key in seen:
            continue
        if label_counts.get(label, 0) >= 2:
            continue
        seen.add(key)
        label_counts[label] = label_counts.get(label, 0) + 1
        selected.append((label, sentence))
        if len(selected) == 3:
            break

    parts = [f"({label}) {sentence}" for label, sentence in selected]
    return "Na podlagi podanega konteksta: " + " ".join(parts)


def is_ambiguous_question(question):
    normalized = " ".join((question or "").lower().strip(" ?!").split())
    return normalized in {
        "kakšen je odpovedni rok",
        "koliko dopusta mi pripada",
        "ali me lahko odpustijo",
        "koliko moram dobiti plače",
    }


def ambiguity_aware_answer(question, results):
    base = extractive_answer(question, results)
    return (
        "Vprašanje je premalo natančno za dokončen odgovor. "
        "Manjkajo konkretne okoliščine, zato lahko navedem samo pravila iz konteksta. "
        + base
    )


def offline_baseline_answer(question):
    q_terms = set(content_terms(question))
    rules = [
        ({"dopust", "letn"}, "Po splošnem pravilu delavcu običajno pripada najmanj 20 dni letnega dopusta, lahko pa tudi več glede na okoliščine."),
        ({"odpovedn", "rok"}, "Odpovedni rok je praviloma 30 dni, vendar je odvisen od pogodbe in delovne dobe."),
        ({"odpoved", "razlog"}, "Delodajalec mora imeti zakonit razlog za odpoved, delavec pa lahko pogodbo odpove tudi brez posebnega razloga."),
        ({"odpravnin"}, "Odpravnina se običajno izračuna glede na povprečno plačo in leta dela pri delodajalcu."),
        ({"pogodb", "pisn"}, "Če pisne pogodbe ni, naj delavec od delodajalca zahteva pisno ureditev delovnega razmerja."),
        ({"poskusn"}, "Poskusno delo lahko traja največ šest mesecev."),
        ({"določen", "čas"}, "Pogodbe za določen čas praviloma ne smejo trajati več kot dve leti."),
        ({"odmor"}, "Delavec ima praviloma pravico do najmanj 30 minut odmora."),
        ({"nadurn"}, "Nadurno delo je omejeno z zakonom in ne sme biti neomejeno."),
        ({"bolnišk", "nadomestil"}, "Nadomestilo za bolniško se najprej krije pri delodajalcu, nato pa iz zdravstvenega zavarovanja."),
        ({"minimaln", "plač", "avstrij"}, "Minimalna plača v Avstriji je določena po kolektivnih pogodbah, zato je treba preveriti panogo."),
        ({"ddv"}, "Za elektronske knjige se pogosto uporablja znižana stopnja DDV, vendar je treba preveriti aktualni zakon."),
        ({"deduj", "stanovanj"}, "Stanovanje po smrti starša dedujejo zakoniti dediči po pravilih dednega prava."),
        ({"družb", "omejen"}, "Družbo z omejeno odgovornostjo se ustanovi z družbeno pogodbo, vpisom v register in osnovnim kapitalom."),
    ]

    for required, answer in rules:
        if required <= q_terms:
            return answer
    return "Nisem povsem prepričan, vendar je odgovor odvisen od konkretnih okoliščin in veljavne zakonodaje."


def offline_answer(question, variant, context, results):
    if variant == "baseline":
        return offline_baseline_answer(question)
    if is_ambiguous_question(question) and context.strip() and results:
        return ambiguity_aware_answer(question, results)
    if should_refuse_from_context(question, context, results):
        return "Iz podanega konteksta ni mogoče zanesljivo odgovoriti."
    return extractive_answer(question, results)


def build_baseline_messages(question):
    return [{"role": "user", "content": f"{BASELINE_PROMPT}\n\nVprašanje: {question}"}]


def build_rag_messages(question, context):
    content = f"{RAG_PROMPT}\n\nKontekst:\n{context}\n\nVprašanje: {question}"
    return [{"role": "user", "content": content}]


def call_answer_model(model_config, messages, options, question, variant, context, results):
    provider = model_config["provider"]
    model = model_config["model"]
    if provider == "offline":
        return offline_answer(question, variant, context, results), "offline", None

    try:
        return chat_model(provider, model, messages, options), provider, None
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        return f"[ERROR: model call failed: {error}]", f"{provider}_error", error


def single_model_config(args, config):
    provider = args.provider or get_default_provider(config)
    model = args.model or get_default_model(config)
    return {
        "model_id": f"{provider}-{model}",
        "display_name": f"{provider}-{model}",
        "provider": provider,
        "model": model,
        "enabled": True,
    }


def selected_model_configs(args, config):
    if args.arena:
        return enabled_arena_models(config)
    return [single_model_config(args, config)]


def add_answer_row(rows, item, variant, prompt_mode, context, answer, model_config, provider_used, options, error=None):
    row = {
        "id": item["id"],
        "variant": variant,
        "question": item["question"],
        "context": context,
        "answer": answer,
        "model_id": model_config["model_id"],
        "display_name": model_config.get("display_name", model_config["model_id"]),
        "provider": provider_used,
        "model": model_config["model"],
        "prompt_mode": prompt_mode,
        "temperature": options["temperature"],
        "top_p": options["top_p"],
        "max_tokens": options["max_tokens"],
        "seed": options["seed"],
        "error": error or "",
    }
    rows.append(row)
    return row


def add_raw_rag_prompt_row(rows, item, context, options):
    raw_prompt = build_rag_messages(item["question"], context)[0]["content"]
    add_answer_row(
        rows,
        item,
        "raw_rag_prompt",
        "raw_rag_prompt",
        context,
        raw_prompt,
        {
            "model_id": "raw-rag-prompt",
            "display_name": "raw RAG prompt",
            "provider": "none",
            "model": "retrieval_prompt",
        },
        "none",
        options,
    )


def parse_args():
    load_env()
    config = load_config()
    defaults = config.get("defaults", {})

    parser = argparse.ArgumentParser(description="Run baseline and RAG answer generation.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--top-k", type=int, default=int(defaults.get("top_k", 3)))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--arena", action="store_true", help="Run all enabled models from evaluation/config.json.")
    parser.add_argument(
        "--raw-rag-prompt",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include the raw RAG prompt as a retrieval-only baseline.",
    )
    parser.add_argument(
        "--provider",
        choices=["offline", "ollama", "openwebui", "openai"],
        default=None,
        help="Provider for single-model mode. Defaults to config/env, normally ollama.",
    )
    parser.add_argument("--model", default=None, help="Model for single-model mode.")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--quiet", action="store_true", help="Disable per-step progress output.")
    parser.set_defaults(_config=config)
    return parser.parse_args()


def main():
    args = parse_args()
    config = args._config
    options = generation_options(config, args)
    questions = load_jsonl(args.questions)
    if args.limit is not None:
        questions = questions[: args.limit]

    chunks = load_chunks()
    index = build_index(chunks)
    model_configs = selected_model_configs(args, config)
    rows = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("", encoding="utf-8")
    include_raw_rag_prompt = (
        config.get("include_raw_rag_prompt", True)
        if args.raw_rag_prompt is None
        else args.raw_rag_prompt
    )

    retrieved = {}
    retrieval_progress = Progress(len(questions), "retrieval") if not args.quiet else None
    for idx, item in enumerate(questions, start=1):
        results = retrieve(item["question"], index, chunks, args.top_k)
        context = format_context(results)
        retrieved[item["id"]] = (results, context)
        if include_raw_rag_prompt:
            add_raw_rag_prompt_row(rows, item, context, options)
            append_jsonl(args.output, rows[-1])
        if retrieval_progress:
            retrieval_progress.log(idx, f"question={item['id']}")

    total_model_calls = len(model_configs) * len(questions) * 2
    generation_progress = Progress(total_model_calls, "answer_generation") if not args.quiet else None
    completed_calls = 0
    for model_index, model_config in enumerate(model_configs, start=1):
        if not args.quiet:
            print(
                f"[model] {model_index}/{len(model_configs)} "
                f"{model_config['model_id']} ({model_config['provider']} / {model_config['model']})",
                flush=True,
            )
        for question_index, item in enumerate(questions, start=1):
            question = item["question"]
            results, context = retrieved[item["id"]]
            baseline_messages = build_baseline_messages(question)
            baseline_answer, baseline_provider, baseline_error = call_answer_model(
                model_config,
                baseline_messages,
                options,
                question,
                "baseline",
                "",
                [],
            )
            add_answer_row(
                rows,
                item,
                "baseline",
                "no_context",
                "",
                baseline_answer,
                model_config,
                baseline_provider,
                options,
                baseline_error,
            )
            append_jsonl(args.output, rows[-1])
            completed_calls += 1
            if generation_progress:
                generation_progress.log(
                    completed_calls,
                    f"model={model_config['model_id']} question={question_index}/{len(questions)} id={item['id']} variant=baseline",
                )

            rag_messages = build_rag_messages(question, context)
            rag_answer, rag_provider, rag_error = call_answer_model(
                model_config,
                rag_messages,
                options,
                question,
                "rag",
                context,
                results,
            )
            add_answer_row(
                rows,
                item,
                "rag",
                "rag_context",
                context,
                rag_answer,
                model_config,
                rag_provider,
                options,
                rag_error,
            )
            append_jsonl(args.output, rows[-1])
            completed_calls += 1
            if generation_progress:
                generation_progress.log(
                    completed_calls,
                    f"model={model_config['model_id']} question={question_index}/{len(questions)} id={item['id']} variant=rag",
                )

    print(f"Saved {len(rows)} answers to {args.output}")
    print(
        f"Questions: {len(questions)} | models: {len(model_configs)} | "
        f"top_k: {args.top_k} | raw_rag_prompt: {include_raw_rag_prompt}"
    )
    for model_config in model_configs:
        print(f"- {model_config['model_id']}: {model_config['provider']} / {model_config['model']}")


if __name__ == "__main__":
    main()

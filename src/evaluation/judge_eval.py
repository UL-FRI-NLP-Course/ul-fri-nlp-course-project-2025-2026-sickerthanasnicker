import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from evaluation.eval_config import (
    EVALUATION_DIR,
    generation_options,
    get_default_judge_model,
    get_default_judge_provider,
    load_config,
    load_env,
)
from evaluation.io_utils import load_jsonl, write_jsonl
from evaluation.model_providers import chat_model
from evaluation.progress_utils import Progress
from evaluation.text_utils import content_terms


DEFAULT_QUESTIONS_FILE = EVALUATION_DIR / "questions.jsonl"
DEFAULT_ANSWERS_FILE = EVALUATION_DIR / "results" / "answers.jsonl"
DEFAULT_OUTPUT_FILE = EVALUATION_DIR / "results" / "judgements.jsonl"

REFUSAL_RE = re.compile(
    r"ni mogoče|ne morem|ni dovolj|ni v kontekstu|ni podan|ne vsebuje|"
    r"ne more zanesljivo|nima odgovora|premalo informacij",
    re.IGNORECASE,
)

CONTEXT_SOURCE_RE = re.compile(
    r"Vir:\s*(?P<label>.*?);\s*(?:tip=(?P<source_type>.*?);\s*)?score=",
    re.IGNORECASE,
)

JUDGE_SYSTEM_PROMPT = """Ocenjuj odgovore na vprašanja iz slovenskega prava.

Pomembno:
- Če vprašanje nima odgovora v kontekstu, mora model to povedati.
- Halucinacije kaznuj strogo.

Vrni JSON rezultat z naslednjimi polji:
{
  "correctness": 0-5,
  "grounding": 0-5,
  "completeness": 0-5,
  "clarity": 0-5,
  "hallucination": 0-5,
  "refusal": true/false,
  "reason": "kratka razlaga"
}

Pri hallucination pomeni 0 brez halucinacij, 5 huda halucinacija."""


def score_overlap(reference, answer):
    reference_terms = set(content_terms(reference))
    if not reference_terms:
        return 0
    answer_terms = set(content_terms(answer))
    fraction = len(reference_terms & answer_terms) / len(reference_terms)
    return max(0, min(5, round(fraction * 5)))


def is_refusal(answer):
    return bool(REFUSAL_RE.search(answer or ""))


def normalize_for_citation(text):
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def context_sources(context):
    sources = []
    for match in CONTEXT_SOURCE_RE.finditer(context or ""):
        label = match.group("label").strip()
        source_type = (match.group("source_type") or "").strip()
        sources.append({"label": label, "source_type": source_type})
    return sources


def question_requests_case_law(question):
    lowered = (question or "").lower()
    return any(term in lowered for term in ("sodna praksa", "sodni praksi", "sodišče", "sodišča", "judikat"))


def source_type_matches_claim(question_item, source_type):
    if question_requests_case_law(question_item.get("question", "")):
        return source_type == "official_case_law"
    return source_type in {"", "primary_law", "official_interpretation", "official_operational_guidance"}


def answer_cites_source(answer, source):
    answer_norm = normalize_for_citation(answer)
    label = source.get("label", "")
    label_norm = normalize_for_citation(label)
    if label_norm and label_norm in answer_norm:
        return True

    law = label.split(", čl.")[0].strip()
    article_match = re.search(r"čl\.\s*([0-9]+[.]?[a-z]?)", label, re.IGNORECASE)
    if article_match:
        return normalize_for_citation(law) in answer_norm and article_match.group(1).lower() in answer_norm

    source_hint = ""
    if "|" in label:
        source_hint = label.split("|")[-1].strip()
    elif "." in label:
        source_hint = label
    return bool(source_hint and normalize_for_citation(source_hint) in answer_norm)


def validate_citation(question_item, answer_item):
    answer = answer_item.get("answer", "")
    if question_item["type"] == "unanswerable" or is_refusal(answer):
        return {
            "citation_required": False,
            "citation_supported": None,
            "citation_reason": "Citation not required for refusal or unanswerable question.",
        }

    sources = context_sources(answer_item.get("context", ""))
    if not sources:
        return {
            "citation_required": True,
            "citation_supported": False,
            "citation_reason": "No parseable retrieved sources in answer context.",
        }

    cited = [source for source in sources if answer_cites_source(answer, source)]
    matching = [source for source in cited if source_type_matches_claim(question_item, source.get("source_type", ""))]
    if matching:
        return {
            "citation_required": True,
            "citation_supported": True,
            "citation_reason": f"Cites matching retrieved source: {matching[0]['label']}.",
        }
    if cited:
        return {
            "citation_required": True,
            "citation_supported": False,
            "citation_reason": "Answer cites a retrieved source, but its source tier does not match the claim type.",
        }
    return {
        "citation_required": True,
        "citation_supported": False,
        "citation_reason": "Supported non-refusal answer does not cite a retrieved source.",
    }


def clarity_score(answer):
    words = (answer or "").split()
    if not words:
        return 0
    if len(words) < 5:
        return 2
    if len(words) > 180:
        return 3
    return 5


def fallback_judge(question_item, answer_item):
    answer = answer_item.get("answer", "")
    context = answer_item.get("context", "")
    reference = question_item["reference"]
    question_type = question_item["type"]
    refused = is_refusal(answer)

    if answer.startswith("[ERROR:"):
        return {
            "correctness": 0,
            "grounding": 0,
            "completeness": 0,
            "clarity": 0,
            "hallucination": 0,
            "refusal": False,
            "reason": "Model call failed; answer was not evaluated semantically.",
        }

    if question_type == "unanswerable":
        correctness = 5 if refused else 1
        grounding = 5 if refused else 1
        completeness = 5 if refused else 1
        hallucination = 0 if refused else 5
        reason = "Unanswerable question: refusal is required." if refused else "Unanswerable question answered without enough context."
    else:
        overlap_score = score_overlap(reference, answer)
        context_terms = set(content_terms(context))
        answer_terms = set(content_terms(answer))
        grounded_fraction = (
            len(answer_terms & context_terms) / len(answer_terms)
            if answer_terms and context_terms
            else 0.0
        )
        grounding = max(0, min(5, round(grounded_fraction * 5)))

        if refused:
            correctness = 1
            completeness = 1
            hallucination = 0
            reason = "Answerable question was refused."
        else:
            correctness = overlap_score
            completeness = overlap_score
            if correctness >= 4 and grounding >= 3:
                hallucination = 0
            elif correctness >= 3:
                hallucination = 2
            elif grounding < 2:
                hallucination = 4
            else:
                hallucination = 3
            reason = "Fallback judge based on keyword overlap with reference and context."

    return {
        "correctness": correctness,
        "grounding": grounding,
        "completeness": completeness,
        "clarity": clarity_score(answer),
        "hallucination": hallucination,
        "refusal": refused,
        "reason": reason,
    }


def build_judge_messages(question_item, answer_item):
    content = f"""{JUDGE_SYSTEM_PROMPT}

Tip vprašanja: {question_item["type"]}
Vprašanje: {question_item["question"]}
Referenca: {question_item["reference"]}
Kontekst:
{answer_item.get("context", "")}

Odgovor modela:
{answer_item.get("answer", "")}
"""
    return [{"role": "user", "content": content}]


def parse_json_response(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError("Judge response did not contain JSON.")
    return json.loads(match.group(0))


def clamp_score(value):
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(5, number))


def normalize_judgement(data):
    return {
        "correctness": clamp_score(data.get("correctness")),
        "grounding": clamp_score(data.get("grounding")),
        "completeness": clamp_score(data.get("completeness")),
        "clarity": clamp_score(data.get("clarity")),
        "hallucination": clamp_score(data.get("hallucination")),
        "refusal": bool(data.get("refusal")),
        "reason": str(data.get("reason", "")),
    }


def enforce_unanswerable_rule(question_item, answer_item, judgement):
    refused = is_refusal(answer_item.get("answer", ""))
    judgement["refusal"] = refused

    if question_item["type"] == "unanswerable":
        if refused:
            judgement["correctness"] = 5
            judgement["grounding"] = 5
            judgement["completeness"] = 5
            judgement["hallucination"] = 0
            judgement["reason"] = (
                judgement.get("reason", "")
                + " Enforced rule: unanswerable question was correctly refused."
            ).strip()
        else:
            judgement["correctness"] = min(judgement["correctness"], 1)
            judgement["hallucination"] = max(judgement["hallucination"], 5)
            judgement["reason"] = (
                judgement.get("reason", "")
                + " Enforced rule: unanswerable question was not refused."
            ).strip()

    return judgement


def judge_answer(question_item, answer_item, provider, model, options):
    if provider == "offline":
        return enforce_unanswerable_rule(
            question_item,
            answer_item,
            fallback_judge(question_item, answer_item),
        ), "offline"

    messages = build_judge_messages(question_item, answer_item)
    try:
        raw = chat_model(provider, model, messages, options)
        judgement = normalize_judgement(parse_json_response(raw))
        return enforce_unanswerable_rule(question_item, answer_item, judgement), provider
    except Exception as exc:
        judgement = fallback_judge(question_item, answer_item)
        judgement["reason"] += f" Judge fallback used after {provider} failure: {type(exc).__name__}: {exc}"
        return enforce_unanswerable_rule(question_item, answer_item, judgement), "offline_fallback"


def apply_citation_validation(question_item, answer_item, judgement):
    citation = validate_citation(question_item, answer_item)
    if citation["citation_required"] and citation["citation_supported"] is False:
        judgement["grounding"] = min(judgement["grounding"], 2)
        judgement["reason"] = (
            judgement.get("reason", "")
            + " Citation validation: "
            + citation["citation_reason"]
        ).strip()
    return {**judgement, **citation}


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        key = (row.get("model_id", row.get("model", "")), row["variant"])
        grouped[key].append(row)

    print("Answer evaluation")
    print(
        f"{'model_id':<24} {'variant':<10} {'n':>3} {'correct':>8} {'ground':>8} "
        f"{'complete':>9} {'clarity':>8} {'halluc':>8} {'refusal':>8}"
    )
    print("-" * 106)

    summary = {}
    for (model_id, variant), items in sorted(grouped.items()):
        n = len(items)
        avg = {}
        for metric in ("correctness", "grounding", "completeness", "clarity", "hallucination"):
            avg[metric] = sum(item[metric] for item in items) / n if n else 0.0

        citation_required = [item for item in items if item.get("citation_required")]
        supported_citation_rate = (
            sum(1 for item in citation_required if item.get("citation_supported")) / len(citation_required)
            if citation_required
            else 0.0
        )
        unanswerable = [item for item in items if item["type"] == "unanswerable"]
        refusal_accuracy = (
            sum(1 for item in unanswerable if item["refusal"]) / len(unanswerable)
            if unanswerable
            else 0.0
        )
        summary[(model_id, variant)] = {
            **avg,
            "supported_citation_rate": supported_citation_rate,
            "refusal_accuracy": refusal_accuracy,
        }

        print(
            f"{model_id:<24} {variant:<10} {n:>3} {avg['correctness']:>8.2f} "
            f"{avg['grounding']:>8.2f} {avg['completeness']:>9.2f} "
            f"{avg['clarity']:>8.2f} {avg['hallucination']:>8.2f} "
            f"{refusal_accuracy:>8.2f}"
        )

    print()
    for model_id in sorted({key[0] for key in summary}):
        baseline = summary.get((model_id, "baseline"))
        rag = summary.get((model_id, "rag"))
        if not baseline or not rag:
            continue
        correctness_delta = rag["correctness"] - baseline["correctness"]
        hallucination_delta = rag["hallucination"] - baseline["hallucination"]
        print(
            f"{model_id}: RAG correctness {correctness_delta:+.2f}, "
            f"hallucination {hallucination_delta:+.2f} (lower is better)"
        )


def parse_args():
    load_env()
    config = load_config()

    parser = argparse.ArgumentParser(description="Judge generated answers and aggregate results.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_FILE)
    parser.add_argument("--answers", type=Path, default=DEFAULT_ANSWERS_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument(
        "--provider",
        choices=["offline", "ollama", "openwebui", "openai"],
        default=None,
        help="Judge provider. Defaults to config/env, normally ollama.",
    )
    parser.add_argument("--model", default=None, help="Judge model.")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--quiet", action="store_true", help="Disable per-answer progress output.")
    parser.set_defaults(_config=config)
    return parser.parse_args()


def main():
    args = parse_args()
    config = args._config
    options = generation_options(config, args)
    provider = args.provider or get_default_judge_provider(config)
    model = args.model or get_default_judge_model(config)

    question_map = {item["id"]: item for item in load_jsonl(args.questions)}
    answers = load_jsonl(args.answers)

    rows = []
    progress = Progress(len(answers), "judge") if not args.quiet else None
    for idx, answer_item in enumerate(answers, start=1):
        question_item = question_map[answer_item["id"]]
        judgement, judge_provider = judge_answer(question_item, answer_item, provider, model, options)
        judgement = apply_citation_validation(question_item, answer_item, judgement)
        passthrough = {
            key: answer_item[key]
            for key in (
                "prompt_id",
                "prompt_label",
                "system_prompt",
                "settings_id",
                "top_k",
                "corpus_path",
            )
            if key in answer_item
        }
        rows.append(
            {
                "id": answer_item["id"],
                "type": question_item["type"],
                "variant": answer_item["variant"],
                "question": answer_item["question"],
                "answer": answer_item["answer"],
                "model_id": answer_item.get("model_id", answer_item.get("model", "")),
                "display_name": answer_item.get("display_name", answer_item.get("model_id", answer_item.get("model", ""))),
                "provider": answer_item.get("provider", ""),
                "model": answer_item.get("model", ""),
                "prompt_mode": answer_item.get("prompt_mode", ""),
                "judge_provider": judge_provider,
                "judge_model": model,
                **passthrough,
                **judgement,
            }
        )
        if progress:
            progress.log(
                idx,
                (
                    f"judge={provider}/{model} answer_model={answer_item.get('model_id', answer_item.get('model', ''))} "
                    f"id={answer_item['id']} variant={answer_item['variant']}"
                ),
            )

    write_jsonl(args.output, rows)
    print(f"Saved {len(rows)} judgements to {args.output}")
    print(f"Judge: {provider} / {model}")
    summarize(rows)


if __name__ == "__main__":
    main()

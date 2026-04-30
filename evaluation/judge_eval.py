import argparse
import json
import os
import re
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path


DEFAULT_QUESTIONS_FILE = Path(__file__).with_name("questions.jsonl")
DEFAULT_ANSWERS_FILE = Path(__file__).with_name("results") / "answers.jsonl"
DEFAULT_OUTPUT_FILE = Path(__file__).with_name("results") / "judgements.jsonl"

TOKEN_RE = re.compile(r"[0-9]+|[A-Za-zČŠŽĆĐčšžćđ]+")
REFUSAL_RE = re.compile(
    r"ni mogoče|ne morem|ni dovolj|ni v kontekstu|ni podan|ne vsebuje|"
    r"ne more zanesljivo|nima odgovora|premalo informacij",
    re.IGNORECASE,
)

STOPWORDS = {
    "ali", "brez", "da", "do", "ga", "gre", "ima", "in", "iz", "je", "jih",
    "jo", "kaj", "kako", "kakšen", "kakšna", "kakšne", "kdaj", "ker", "ki",
    "ko", "kolikšna", "koliko", "lahko", "me", "med", "mi", "mora", "moram",
    "na", "nad", "ne", "ni", "o", "ob", "od", "po", "pod", "pri", "se",
    "so", "s", "sta", "te", "ter", "to", "v", "vprašanje", "za", "z", "že",
    "kontekst", "zanesljivo", "odgovoriti", "pove", "danega", "korpusa",
}

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


def load_jsonl(path):
    with open(path, encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


def stem_token(token):
    token = token.lower()
    for suffix in (
        "skega", "skem", "skih", "ostjo", "anje", "enega", "ega", "imi",
        "ami", "ijo", "ost", "ih", "im", "em", "om", "a", "e", "i", "o", "u",
    ):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def content_terms(text):
    terms = []
    for token in TOKEN_RE.findall(text.lower()):
        if token in STOPWORDS:
            continue
        if len(token) <= 2 and not token.isdigit():
            continue
        terms.append(stem_token(token))
    return terms


def score_overlap(reference, answer):
    reference_terms = set(content_terms(reference))
    if not reference_terms:
        return 0
    answer_terms = set(content_terms(answer))
    fraction = len(reference_terms & answer_terms) / len(reference_terms)
    return max(0, min(5, round(fraction * 5)))


def is_refusal(answer):
    return bool(REFUSAL_RE.search(answer or ""))


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


def call_openai(prompt, model):
    from openai import OpenAI

    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=prompt,
        temperature=0,
    )
    if hasattr(response, "output_text"):
        return response.output_text.strip()
    return str(response).strip()


def call_ollama(prompt, model):
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0},
    }
    request = urllib.request.Request(
        f"{host}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data.get("response", "").strip()


def resolve_provider(provider, model):
    if provider != "auto":
        return provider
    if os.environ.get("OPENAI_API_KEY") and model:
        return "openai"
    if model and (os.environ.get("OLLAMA_HOST") or os.environ.get("OLLAMA_MODEL")):
        return "ollama"
    return "offline"


def build_judge_prompt(question_item, answer_item):
    return f"""{JUDGE_SYSTEM_PROMPT}

Tip vprašanja: {question_item["type"]}
Vprašanje: {question_item["question"]}
Referenca: {question_item["reference"]}
Kontekst:
{answer_item.get("context", "")}

Odgovor modela:
{answer_item.get("answer", "")}
"""


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


def judge_answer(question_item, answer_item, provider, model):
    resolved = resolve_provider(provider, model)
    if resolved == "offline":
        judgement = fallback_judge(question_item, answer_item)
        return judgement, "offline"

    prompt = build_judge_prompt(question_item, answer_item)
    try:
        if resolved == "openai":
            raw = call_openai(prompt, model)
        elif resolved == "ollama":
            raw = call_ollama(prompt, model)
        else:
            raw = ""
        judgement = normalize_judgement(parse_json_response(raw))
        return judgement, resolved
    except Exception as exc:
        judgement = fallback_judge(question_item, answer_item)
        judgement["reason"] += f" Judge fallback used after {resolved} failure: {exc}"
        return judgement, "offline_fallback"


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["variant"]].append(row)

    print("Answer evaluation")
    print(
        f"{'variant':<12} {'n':>3} {'correct':>8} {'ground':>8} "
        f"{'complete':>9} {'clarity':>8} {'halluc':>8} {'refusal':>8}"
    )
    print("-" * 78)

    summary = {}
    for variant, items in sorted(grouped.items()):
        n = len(items)
        avg = {}
        for metric in ("correctness", "grounding", "completeness", "clarity", "hallucination"):
            avg[metric] = sum(item[metric] for item in items) / n if n else 0.0

        unanswerable = [item for item in items if item["type"] == "unanswerable"]
        refusal_accuracy = (
            sum(1 for item in unanswerable if item["refusal"]) / len(unanswerable)
            if unanswerable
            else 0.0
        )
        summary[variant] = {**avg, "refusal_accuracy": refusal_accuracy}

        print(
            f"{variant:<12} {n:>3} {avg['correctness']:>8.2f} "
            f"{avg['grounding']:>8.2f} {avg['completeness']:>9.2f} "
            f"{avg['clarity']:>8.2f} {avg['hallucination']:>8.2f} "
            f"{refusal_accuracy:>8.2f}"
        )

    if "baseline" in summary and "rag" in summary:
        correctness_delta = summary["rag"]["correctness"] - summary["baseline"]["correctness"]
        hallucination_delta = summary["rag"]["hallucination"] - summary["baseline"]["hallucination"]
        print()
        print(f"RAG vs baseline correctness delta: {correctness_delta:+.2f}")
        print(f"RAG vs baseline hallucination delta: {hallucination_delta:+.2f} (lower is better)")


def parse_args():
    parser = argparse.ArgumentParser(description="Judge generated answers and aggregate results.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_FILE)
    parser.add_argument("--answers", type=Path, default=DEFAULT_ANSWERS_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument(
        "--provider",
        choices=["auto", "offline", "openai", "ollama"],
        default=os.environ.get("JUDGE_PROVIDER", os.environ.get("EVAL_PROVIDER", "auto")),
    )
    parser.add_argument("--model", default=os.environ.get("JUDGE_MODEL") or os.environ.get("EVAL_MODEL") or os.environ.get("OLLAMA_MODEL"))
    return parser.parse_args()


def main():
    args = parse_args()
    question_map = {item["id"]: item for item in load_jsonl(args.questions)}
    answers = load_jsonl(args.answers)

    rows = []
    for answer_item in answers:
        question_item = question_map[answer_item["id"]]
        judgement, judge_provider = judge_answer(question_item, answer_item, args.provider, args.model)
        rows.append(
            {
                "id": answer_item["id"],
                "type": question_item["type"],
                "variant": answer_item["variant"],
                "question": answer_item["question"],
                "answer": answer_item["answer"],
                "judge_provider": judge_provider,
                **judgement,
            }
        )

    write_jsonl(args.output, rows)
    print(f"Saved {len(rows)} judgements to {args.output}")
    summarize(rows)


if __name__ == "__main__":
    main()

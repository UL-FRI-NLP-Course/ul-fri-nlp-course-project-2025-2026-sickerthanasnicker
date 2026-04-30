import argparse
import csv
import hashlib
import json
import random
import re
from collections import defaultdict
from pathlib import Path

from eval_config import generation_options, load_config, load_env
from io_utils import append_jsonl, load_jsonl
from judge_eval import fallback_judge
from model_providers import chat_model
from progress_utils import Progress
from retrieval_shared import build_index, format_context, load_chunks, retrieve


DEFAULT_QUESTIONS_FILE = Path(__file__).with_name("questions.jsonl")
DEFAULT_ANSWERS_FILE = Path(__file__).with_name("results") / "answers.jsonl"
DEFAULT_OUTPUT_FILE = Path(__file__).with_name("results") / "vote_eval.jsonl"
DEFAULT_SUMMARY_FILE = Path(__file__).with_name("results") / "vote_summary.csv"

VOTE_SYSTEM_PROMPT = """Ocenjuješ anonimne odgovore na vprašanja iz slovenskega prava.

Pravila:
- Uporabi samo podani kontekst.
- Najboljši odgovor je pravilen, utemeljen v kontekstu, jasen in popoln.
- Če kontekst ne vsebuje odgovora, mora najboljši odgovor to jasno povedati.
- Halucinacije ali nepodprte pravne trditve strogo kaznuj.

Vrni JSON:
{
  "ranking": ["A", "B", "C"],
  "reason": "kratka razlaga"
}
"""


def stable_seed(*parts):
    raw = "|".join(str(part) for part in parts)
    return int(hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12], 16)


def candidate_id(row, index):
    parts = [row.get("model_id") or row.get("model") or f"candidate-{index}"]
    for key in ("prompt_id", "settings_id"):
        if row.get(key):
            parts.append(row[key])
    return "::".join(parts)


def answer_ok(row):
    answer = row.get("answer", "")
    return answer and not answer.startswith("[ERROR:") and not row.get("error")


def group_candidates(rows, variants, exclude_raw_prompt, max_candidates):
    groups = defaultdict(list)
    for index, row in enumerate(rows, start=1):
        variant = row.get("variant", "")
        if variants and variant not in variants:
            continue
        if exclude_raw_prompt and variant == "raw_rag_prompt":
            continue
        if not answer_ok(row):
            continue
        candidate = dict(row)
        candidate["candidate_id"] = candidate_id(row, index)
        groups[(candidate["id"], variant)].append(candidate)

    result = {}
    for key, items in groups.items():
        seen = set()
        deduped = []
        for item in items:
            identity = item["candidate_id"]
            if identity in seen:
                continue
            seen.add(identity)
            deduped.append(item)
        result[key] = deduped[:max_candidates] if max_candidates else deduped
    return result


def derive_voters(groups, provider_override=None, model_override=None):
    voters = {}
    for candidates in groups.values():
        for row in candidates:
            model_id = row.get("model_id") or row.get("model")
            if not model_id or model_id in voters:
                continue
            provider = provider_override or row.get("provider") or "offline"
            model = model_override or row.get("model") or "offline"
            if provider.endswith("_error") or provider == "none":
                provider = provider_override or "offline"
                model = model_override or "offline"
            voters[model_id] = {
                "voter_model_id": model_id,
                "provider": provider,
                "model": model,
                "display_name": row.get("display_name", model_id),
            }
    return list(voters.values())


def anonymize_candidates(question_id, variant, candidates, seed):
    labels = [chr(ord("A") + idx) for idx in range(len(candidates))]
    shuffled = list(candidates)
    rng = random.Random(seed + stable_seed(question_id, variant))
    rng.shuffle(shuffled)
    return [
        {
            "label": labels[idx],
            "candidate": candidate,
        }
        for idx, candidate in enumerate(shuffled)
    ]


def build_vote_messages(question_item, context, anonymous_candidates):
    answers = []
    for item in anonymous_candidates:
        answers.append(f"{item['label']}) {item['candidate']['answer']}")
    content = f"""Tip vprašanja: {question_item['type']}
Vprašanje: {question_item['question']}

Kontekst:
{context}

Anonimni odgovori:
{chr(10).join(answers)}
"""
    return [
        {"role": "system", "content": VOTE_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


def parse_ranking(text, valid_labels):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        data = json.loads(match.group(0))
        ranking = data.get("ranking", [])
        reason = str(data.get("reason", ""))
    else:
        ranking = re.findall(r"\b[A-Z]\b", cleaned)
        reason = "Parsed ranking labels from non-JSON response."

    seen = set()
    normalized = []
    for label in ranking:
        label = str(label).strip().upper()
        if label in valid_labels and label not in seen:
            normalized.append(label)
            seen.add(label)
    for label in valid_labels:
        if label not in seen:
            normalized.append(label)
    return normalized, reason


def offline_ranking(question_item, context, anonymous_candidates):
    scored = []
    for item in anonymous_candidates:
        candidate = dict(item["candidate"])
        candidate["context"] = context
        judgement = fallback_judge(question_item, candidate)
        score = (
            judgement["correctness"]
            + judgement["grounding"]
            + judgement["completeness"]
            + judgement["clarity"] * 0.25
            - judgement["hallucination"]
        )
        scored.append((score, item["label"]))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [label for _score, label in scored], "Offline deterministic ranking from fallback judge scores."


def vote(voter, question_item, context, anonymous_candidates, options):
    if voter["provider"] == "offline":
        return offline_ranking(question_item, context, anonymous_candidates), "offline", ""
    try:
        raw = chat_model(
            voter["provider"],
            voter["model"],
            build_vote_messages(question_item, context, anonymous_candidates),
            options,
        )
        labels = [item["label"] for item in anonymous_candidates]
        ranking, reason = parse_ranking(raw, labels)
        return (ranking, reason), voter["provider"], ""
    except Exception as exc:
        ranking, reason = offline_ranking(question_item, context, anonymous_candidates)
        error = f"{type(exc).__name__}: {exc}"
        return (ranking, f"{reason} Live voter failed: {error}"), "offline_fallback", error


def ranking_to_scores(ranking):
    n = len(ranking)
    if n <= 1:
        return {ranking[0]: 1.0} if ranking else {}
    return {label: (n - rank) / (n - 1) for rank, label in enumerate(ranking, start=1)}


def make_vote_row(question_item, variant, context, voter, anonymous_candidates, ranking, reason, provider_used, error):
    scores = ranking_to_scores(ranking)
    by_label = {item["label"]: item["candidate"] for item in anonymous_candidates}
    candidate_scores = []
    for rank, label in enumerate(ranking, start=1):
        candidate = by_label[label]
        candidate_scores.append(
            {
                "label": label,
                "rank": rank,
                "score": round(scores[label], 4),
                "candidate_id": candidate["candidate_id"],
                "candidate_model_id": candidate.get("model_id", ""),
                "candidate_display_name": candidate.get("display_name", candidate.get("model_id", "")),
                "candidate_variant": candidate.get("variant", variant),
                "candidate_prompt_id": candidate.get("prompt_id", ""),
                "candidate_settings_id": candidate.get("settings_id", ""),
                "is_self_vote": candidate.get("model_id") == voter["voter_model_id"],
            }
        )
    return {
        "id": question_item["id"],
        "type": question_item["type"],
        "variant": variant,
        "question": question_item["question"],
        "context": context,
        "voter_model_id": voter["voter_model_id"],
        "voter_display_name": voter.get("display_name", voter["voter_model_id"]),
        "voter_provider": provider_used,
        "voter_model": voter["model"],
        "ranking": ranking,
        "candidate_scores": candidate_scores,
        "reason": reason,
        "error": error,
    }


def summarize_votes(vote_rows, summary_output):
    totals = defaultdict(list)
    self_scores = defaultdict(list)
    other_scores = defaultdict(list)
    ranks = defaultdict(list)
    self_ranks = defaultdict(list)
    other_ranks = defaultdict(list)
    labels = {}

    for row in vote_rows:
        for candidate in row["candidate_scores"]:
            key = (
                candidate["candidate_id"],
                candidate["candidate_model_id"],
                row["variant"],
            )
            labels[key] = candidate["candidate_display_name"]
            totals[key].append(candidate["score"])
            ranks[key].append(candidate["rank"])
            if candidate["is_self_vote"]:
                self_scores[key].append(candidate["score"])
                self_ranks[key].append(candidate["rank"])
            else:
                other_scores[key].append(candidate["score"])
                other_ranks[key].append(candidate["rank"])

    columns = [
        "candidate_id",
        "candidate_model_id",
        "candidate_display_name",
        "variant",
        "n_votes",
        "vote_score_mean",
        "normalized_vote_score",
        "vote_score_by_other_models",
        "self_vote_score",
        "self_bias",
        "rank_mean",
        "rank_by_other_models",
        "self_rank_mean",
        "self_rank_delta",
    ]
    summary_output.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_output, "w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        for key in sorted(totals):
            candidate_id_value, candidate_model_id, variant = key
            mean = average(totals[key])
            other = average(other_scores[key])
            own = average(self_scores[key])
            rank_mean = average(ranks[key])
            other_rank = average(other_ranks[key])
            own_rank = average(self_ranks[key])
            writer.writerow(
                {
                    "candidate_id": candidate_id_value,
                    "candidate_model_id": candidate_model_id,
                    "candidate_display_name": labels.get(key, candidate_model_id),
                    "variant": variant,
                    "n_votes": len(totals[key]),
                    "vote_score_mean": round(mean, 4),
                    "normalized_vote_score": round(mean, 4),
                    "vote_score_by_other_models": round(other, 4) if other is not None else "",
                    "self_vote_score": round(own, 4) if own is not None else "",
                    "self_bias": round(own - other, 4) if own is not None and other is not None else "",
                    "rank_mean": round(rank_mean, 4),
                    "rank_by_other_models": round(other_rank, 4) if other_rank is not None else "",
                    "self_rank_mean": round(own_rank, 4) if own_rank is not None else "",
                    "self_rank_delta": round(own_rank - other_rank, 4) if own_rank is not None and other_rank is not None else "",
                }
            )


def average(values):
    if not values:
        return None
    return sum(values) / len(values)


def parse_args():
    load_env()
    config = load_config()
    parser = argparse.ArgumentParser(description="Run anonymized model vote ranking over existing answers.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_FILE)
    parser.add_argument("--answers", type=Path, default=DEFAULT_ANSWERS_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_FILE)
    parser.add_argument("--variant", action="append", default=None, help="Answer variant to rank. Repeatable. Defaults to rag.")
    parser.add_argument("--top-k", type=int, default=int(config.get("defaults", {}).get("top_k", 3)))
    parser.add_argument("--limit", type=int, default=None, help="Limit number of question/variant groups.")
    parser.add_argument("--max-candidates", type=int, default=8)
    parser.add_argument("--include-singletons", action="store_true")
    parser.add_argument("--include-raw-prompt", action="store_true")
    parser.add_argument("--provider", choices=["offline", "ollama", "openwebui", "openai"], default=None)
    parser.add_argument("--model", default=None, help="Override voter model when --provider is set.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--quiet", action="store_true", help="Disable per-vote progress output.")
    parser.set_defaults(_config=config)
    return parser.parse_args()


def main():
    args = parse_args()
    variants = args.variant or ["rag"]
    options = generation_options(args._config, args)
    question_map = {item["id"]: item for item in load_jsonl(args.questions)}
    answer_rows = load_jsonl(args.answers)
    groups = group_candidates(answer_rows, variants, not args.include_raw_prompt, args.max_candidates)
    groups = {
        key: candidates
        for key, candidates in groups.items()
        if args.include_singletons or len(candidates) >= 2
    }
    group_items = list(groups.items())
    if args.limit is not None:
        group_items = group_items[: args.limit]

    voters = derive_voters(dict(group_items), args.provider, args.model)
    chunks = load_chunks()
    index = build_index(chunks)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("", encoding="utf-8")
    total_votes = len(group_items) * len(voters)
    progress = Progress(total_votes, "vote_eval") if not args.quiet else None
    vote_rows = []
    completed = 0

    print(
        f"Vote evaluation groups={len(group_items)} voters={len(voters)} variants={','.join(variants)} output={args.output}",
        flush=True,
    )
    for (question_id, variant), candidates in group_items:
        question_item = question_map[question_id]
        results = retrieve(question_item["question"], index, chunks, args.top_k)
        context = format_context(results)
        anonymous = anonymize_candidates(question_id, variant, candidates, args.seed)
        for voter in voters:
            (ranking, reason), provider_used, error = vote(voter, question_item, context, anonymous, options)
            row = make_vote_row(question_item, variant, context, voter, anonymous, ranking, reason, provider_used, error)
            append_jsonl(args.output, row)
            vote_rows.append(row)
            completed += 1
            if progress:
                progress.log(
                    completed,
                    f"voter={voter['voter_model_id']} question={question_id} variant={variant} candidates={len(candidates)}",
                )

    summarize_votes(vote_rows, args.summary_output)
    print(f"Saved {len(vote_rows)} vote rows to {args.output}")
    print(f"Saved vote summary to {args.summary_output}")


if __name__ == "__main__":
    main()

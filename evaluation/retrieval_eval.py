import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_CODE_DIR = PROJECT_ROOT / "report" / "code"
CHUNKS_FILE = REPORT_CODE_DIR / "data" / "chunk.jsonl"
DEFAULT_QUESTIONS_FILE = Path(__file__).with_name("questions.jsonl")
DEFAULT_OUTPUT_FILE = Path(__file__).with_name("results") / "retrieval.jsonl"

TOKEN_RE = re.compile(r"[0-9]+|[A-Za-zČŠŽĆĐčšžćđ]+")

STOPWORDS = {
    "ali", "brez", "da", "do", "ga", "gre", "ima", "in", "iz", "je", "jih",
    "jo", "kaj", "kako", "kakšen", "kakšna", "kakšne", "kdaj", "ker", "ki",
    "ko", "kolikšna", "koliko", "lahko", "me", "med", "mi", "mora", "moram",
    "na", "nad", "ne", "ni", "o", "ob", "od", "po", "pod", "pri", "se",
    "so", "s", "sta", "te", "ter", "to", "v", "vprašanje", "za", "z", "že",
    "kontekst", "zanesljivo", "odgovoriti", "pove", "danega", "korpusa",
}


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


class SimpleLexicalIndex:
    def __init__(self, tokenized_docs):
        self.docs = [Counter(content_terms(" ".join(doc))) for doc in tokenized_docs]

    def get_scores(self, query_tokens):
        query_terms = set(content_terms(" ".join(query_tokens)))
        return [sum(doc.get(term, 0) for term in query_terms) for doc in self.docs]


def build_index(chunks):
    tokenized = [chunk["text"].lower().split() for chunk in chunks]
    try:
        from rank_bm25 import BM25Okapi

        return BM25Okapi(tokenized)
    except ImportError:
        return SimpleLexicalIndex(tokenized)


def load_project_search():
    sys.path.insert(0, str(REPORT_CODE_DIR))
    try:
        from rag import search

        return search
    except Exception:
        return None


def fallback_search(query, index, chunks, top_k=3):
    scores = index.get_scores(query.lower().split())
    ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)[:top_k]
    return [(chunks[i], round(float(score), 3)) for i, score in ranked]


def retrieve(query, index, chunks, top_k):
    project_search = load_project_search()
    if project_search is not None:
        return project_search(query, index, chunks, top_k=top_k)
    return fallback_search(query, index, chunks, top_k=top_k)


def source_label(chunk):
    meta = chunk.get("meta", {})
    law = meta.get("law") or "neznan vir"
    article = meta.get("article")
    if article:
        return f"{law}, čl. {article}"
    return law


def format_context(results):
    blocks = []
    for rank, (chunk, score) in enumerate(results, start=1):
        blocks.append(
            f"[{rank}] Vir: {source_label(chunk)}; score={score}\n{chunk['text']}"
        )
    return "\n\n".join(blocks)


def keyword_hit(reference, context, threshold):
    keywords = set(content_terms(reference))
    if not keywords:
        return False, 0.0, []

    context_terms = set(content_terms(context))
    matches = sorted(keywords & context_terms)
    fraction = len(matches) / len(keywords)
    return fraction >= threshold, fraction, matches


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.35)
    return parser.parse_args()


def main():
    args = parse_args()
    questions = load_jsonl(args.questions)
    chunks = load_jsonl(CHUNKS_FILE)
    index = build_index(chunks)

    rows = []
    answerable_hits = []
    unanswerable_false_hits = []
    context_lengths = []

    for item in questions:
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
                "top_sources": [
                    {"source": source_label(chunk), "score": float(score)}
                    for chunk, score in results
                ],
            }
        )

    write_jsonl(args.output, rows)

    hit_rate = sum(answerable_hits) / len(answerable_hits) if answerable_hits else 0.0
    false_hit_rate = (
        sum(unanswerable_false_hits) / len(unanswerable_false_hits)
        if unanswerable_false_hits
        else 0.0
    )
    avg_context_length = sum(context_lengths) / len(context_lengths) if context_lengths else 0.0

    print("Retrieval evaluation")
    print(f"questions: {len(questions)} | top_k: {args.top_k} | output: {args.output}")
    print(f"answerable hit rate: {hit_rate:.3f}")
    print(f"unanswerable false evidence rate: {false_hit_rate:.3f}")
    print(f"average context length: {avg_context_length:.1f} words")


if __name__ == "__main__":
    main()

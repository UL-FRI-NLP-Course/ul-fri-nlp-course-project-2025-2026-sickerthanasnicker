import sys
from collections import Counter
from pathlib import Path

from io_utils import load_jsonl
from text_utils import content_terms


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_CODE_DIR = PROJECT_ROOT / "report" / "code"
CHUNKS_FILE = REPORT_CODE_DIR / "data" / "chunk.jsonl"


class SimpleLexicalIndex:
    """Small fallback used when rank-bm25 is not installed."""

    def __init__(self, tokenized_docs):
        self.docs = [Counter(content_terms(" ".join(doc))) for doc in tokenized_docs]

    def get_scores(self, query_tokens):
        query_terms = set(content_terms(" ".join(query_tokens)))
        return [sum(doc.get(term, 0) for term in query_terms) for doc in self.docs]


def load_chunks(path=CHUNKS_FILE):
    return load_jsonl(path)


def build_index(chunks):
    tokenizer = load_project_tokenizer() or content_terms
    tokenized = [tokenizer(chunk["text"]) for chunk in chunks]
    try:
        from rank_bm25 import BM25Okapi

        return BM25Okapi(tokenized)
    except ImportError:
        return SimpleLexicalIndex(tokenized)


def load_project_search():
    if str(REPORT_CODE_DIR) not in sys.path:
        sys.path.insert(0, str(REPORT_CODE_DIR))
    try:
        from rag import search

        return search
    except Exception:
        return None


def load_project_tokenizer():
    if str(REPORT_CODE_DIR) not in sys.path:
        sys.path.insert(0, str(REPORT_CODE_DIR))
    try:
        from rag import tokenize

        return tokenize
    except Exception:
        return None


def fallback_search(query, index, chunks, top_k=3):
    tokenizer = load_project_tokenizer() or content_terms
    scores = index.get_scores(tokenizer(query))
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
        meta = chunk.get("meta", {})
        source_type = meta.get("source_type", "unknown")
        url = meta.get("url", "")
        blocks.append(
            f"[{rank}] Vir: {source_label(chunk)}; tip={source_type}; score={score}; url={url}\n{chunk['text']}"
        )
    return "\n\n".join(blocks)

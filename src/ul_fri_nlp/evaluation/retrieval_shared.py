from ul_fri_nlp.app.rag import CHUNKS_FILE, build_search_index, search
from ul_fri_nlp.evaluation.io_utils import load_jsonl


def load_chunks(path=CHUNKS_FILE):
    return load_jsonl(path)


def build_index(chunks):
    return build_search_index(chunks)


def retrieve(query, index, chunks, top_k):
    return search(query, index, chunks, top_k=top_k)


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

import json
import sys
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi

CHUNKS_FILE = "data/chunk.jsonl"
INDEX_FILE = "data/index.pkl"

KEYWORDS = [
    "delovno razmerje", "pogodba o zaposlitvi", "odpoved", "odpovedni rok",
    "letni dopust", "dopust", "delavec", "delodajalec", "plača", "bolezninska",
    "nadurno delo", "odpravnina", "minimalna plača", "ZDR", "delovni čas"
]


def is_relevant(text):
    t = text.lower()
    return any(k in t for k in KEYWORDS)


def chunk_text(text, size=300):
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - 30):
        chunks.append(" ".join(words[i:i+size]))
    return chunks


def build_index(jsonl_dir):
    print("Filtriram in gradim index...")
    Path("data").mkdir(exist_ok=True)

    chunks = []
    for f in Path(jsonl_dir).glob("*.jsonl"):
        print(f"  {f.name}")
        with open(f, encoding="utf-8") as fp:
            for line in fp:
                try:
                    doc = json.loads(line)
                except:
                    continue
                text = doc.get("text") or doc.get("vsebina") or doc.get("content") or ""
                if not text or not is_relevant(text):
                    continue
                meta = {
                    "law": doc.get("naziv") or doc.get("title") or "",
                    "article": doc.get("clen") or doc.get("article") or "",
                    "source": doc.get("source") or f.name,
                }
                for chunk in chunk_text(text):
                    chunks.append({"text": chunk, "meta": meta})

    print(f"Najdenih chunkov: {len(chunks)}")

    with open(CHUNKS_FILE, "w", encoding="utf-8") as fp:
        for c in chunks:
            fp.write(json.dumps(c, ensure_ascii=False) + "\n")

    tokenized = [c["text"].lower().split() for c in chunks]
    index = BM25Okapi(tokenized)

    with open(INDEX_FILE, "wb") as fp:
        pickle.dump((index, chunks), fp)

    print("Index shranjen.")


def build_index_from_chunks():
    print("Gradim index iz chunks.jsonl...")
    chunks = []
    with open(CHUNKS_FILE, encoding="utf-8") as fp:
        for line in fp:
            chunks.append(json.loads(line))
    tokenized = [c["text"].lower().split() for c in chunks]
    index = BM25Okapi(tokenized)
    with open(INDEX_FILE, "wb") as fp:
        pickle.dump((index, chunks), fp)
    print(f"Index zgrajen ({len(chunks)} chunkov).\n")


def load_index():
    with open(INDEX_FILE, "rb") as fp:
        return pickle.load(fp)


def search(query, index, chunks, top_k=3):
    scores = index.get_scores(query.lower().split())
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [(chunks[i], round(s, 3)) for i, s in ranked]


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--build":
        if len(sys.argv) < 3:
            print("Uporaba: python rag.py --build <pot_do_coleslaw>")
            return
        build_index(sys.argv[2])
        return

    # ce index ne obstaja ampak chunks.jsonl je ze tam, ga zgradi avtomatsko
    if not Path(INDEX_FILE).exists() and Path(CHUNKS_FILE).exists():
        build_index_from_chunks()

    if not Path(INDEX_FILE).exists():
        print("Index ne obstaja. Najprej zaženi: python rag.py --build <pot_do_coleslaw>")
        return

    index, chunks = load_index()

    print("Pravni asistent (delovno pravo) — za izhod vtipkaj 'exit'\n")
    while True:
        query = input("Vprašanje: ").strip()
        if query.lower() in ("exit", "quit", "izhod"):
            break
        if not query:
            continue

        results = search(query, index, chunks)
        print()
        for i, (chunk, score) in enumerate(results):
            m = chunk["meta"]
            ref = m["law"] + (f", čl. {m['article']}" if m["article"] else "")
            print(f"[{i+1}] {ref} (score: {score})")
            print(f"    {chunk['text'][:300]}")
            print()


if __name__ == "__main__":
    main()
import json
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi

CHUNKS_FILE = "data/chunks.jsonl"
INDEX_FILE = "data/index.pkl"

TEST_QUERIES = [
    "Koliko dni letnega dopusta mi pripada?",
    "Koliko znaša odpovedni rok?",
    "Ali me delodajalec lahko odpusti brez razloga?",
    "Koliko znaša odpravnina?",
    "Kaj se zgodi če nimam pisne pogodbe?",
    "Ali mi med bolniško lahko odpovejo pogodbo?",
    "Kdaj ima delavec pravico do izredne odpovedi?",
    "Koliko časa je lahko pogodba za določen čas?",
    "Ali imam pravico do odmora med delom?",
    "Koliko dopusta mi pripada če sem zaposlen pol leta?",
]


def load_index():
    with open(INDEX_FILE, "rb") as f:
        return pickle.load(f)


def build_if_needed():
    if not Path(INDEX_FILE).exists():
        print("Gradim index...")
        chunks = []
        with open(CHUNKS_FILE, encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line))
        index = BM25Okapi([c["text"].lower().split() for c in chunks])
        with open(INDEX_FILE, "wb") as f:
            pickle.dump((index, chunks), f)


def search(query, index, chunks, top_k=3):
    scores = index.get_scores(query.lower().split())
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
    return [(chunks[i], round(s, 3)) for i, s in ranked]


def main():
    build_if_needed()
    index, chunks = load_index()

    print(f"{'Query':<45} {'Top result':<30} {'Score'}")
    print("-" * 85)

    for q in TEST_QUERIES:
        results = search(q, index, chunks)
        top, score = results[0]
        m = top["meta"]
        ref = m["law"] + (f" čl. {m['article']}" if m["article"] else "")
        print(f"{q:<45} {ref:<30} {score}")

    print()
    print(f"Skupaj queriev: {len(TEST_QUERIES)}, chunkov v indexu: {len(chunks)}")


if __name__ == "__main__":
    main()

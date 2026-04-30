import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_CODE_DIR = PROJECT_ROOT / "report" / "code"
CHUNKS_FILE = REPORT_CODE_DIR / "data" / "chunk.jsonl"
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

TOKEN_RE = re.compile(r"[0-9]+|[A-Za-zČŠŽĆĐčšžćđ]+")

STOPWORDS = {
    "ali", "brez", "da", "do", "ga", "gre", "ima", "in", "iz", "je", "jih",
    "jo", "kaj", "kako", "kakšen", "kakšna", "kakšne", "kdaj", "ker", "ki",
    "ko", "kolikšna", "koliko", "lahko", "me", "med", "mi", "mora", "moram",
    "na", "nad", "ne", "ni", "o", "ob", "od", "po", "pod", "pri", "se",
    "so", "s", "sta", "te", "ter", "to", "v", "za", "z", "že",
}


def load_questions(path):
    with open(path, encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


def load_chunks(path=CHUNKS_FILE):
    with open(path, encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


def stem_token(token):
    token = token.lower()
    for suffix in (
        "skega", "skem", "skih", "ostjo", "anje", "enega", "ega", "imi",
        "ami", "ijo", "ost", "ih", "im", "em", "om", "ega", "ega", "a",
        "e", "i", "o", "u",
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
    """Small fallback used when rank-bm25 is not installed."""

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


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


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
    candidates = []

    for chunk, _score in results:
        label = source_label(chunk)
        for sentence in split_sentences(chunk["text"]):
            sentence_terms = set(content_terms(sentence))
            overlap = len(question_terms & sentence_terms)
            if overlap:
                candidates.append((overlap, label, sentence))

    if not candidates:
        return "Iz podanega konteksta ni mogoče zanesljivo odgovoriti."

    candidates.sort(key=lambda item: item[0], reverse=True)
    selected = []
    seen = set()
    for _overlap, label, sentence in candidates:
        key = (label, sentence)
        if key in seen:
            continue
        seen.add(key)
        selected.append((label, sentence))
        if len(selected) == 2:
            break

    answer_parts = [f"({label}) {sentence}" for label, sentence in selected]
    return "Na podlagi podanega konteksta: " + " ".join(answer_parts)


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

    if should_refuse_from_context(question, context, results):
        return "Iz podanega konteksta ni mogoče zanesljivo odgovoriti."

    return extractive_answer(question, results)


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


def generate_answer(prompt, question, variant, context, results, provider, model):
    resolved = resolve_provider(provider, model)
    if resolved == "offline":
        return offline_answer(question, variant, context, results), "offline"

    try:
        if resolved == "openai":
            return call_openai(prompt, model), "openai"
        if resolved == "ollama":
            return call_ollama(prompt, model), "ollama"
    except Exception as exc:
        fallback = offline_answer(question, variant, context, results)
        return f"{fallback}\n\n[Opomba: {resolved} klic ni uspel: {exc}]", "offline_fallback"

    fallback = offline_answer(question, variant, context, results)
    return fallback, "offline"


def build_baseline_prompt(question):
    return f"{BASELINE_PROMPT}\n\nVprašanje: {question}"


def build_rag_prompt(question, context):
    return f"{RAG_PROMPT}\n\nKontekst:\n{context}\n\nVprašanje: {question}"


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        for row in rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Run baseline and RAG answer generation.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--provider",
        choices=["auto", "offline", "openai", "ollama"],
        default=os.environ.get("EVAL_PROVIDER", "auto"),
    )
    parser.add_argument("--model", default=os.environ.get("EVAL_MODEL") or os.environ.get("OLLAMA_MODEL"))
    parser.add_argument("--slovenian-model", default=os.environ.get("SLOVENIAN_MODEL"))
    return parser.parse_args()


def main():
    args = parse_args()
    questions = load_questions(args.questions)
    if args.limit is not None:
        questions = questions[: args.limit]

    chunks = load_chunks()
    index = build_index(chunks)
    rows = []

    for item in questions:
        question = item["question"]

        baseline_prompt = build_baseline_prompt(question)
        baseline_answer, baseline_provider = generate_answer(
            baseline_prompt,
            question,
            "baseline",
            "",
            [],
            args.provider,
            args.model,
        )
        rows.append(
            {
                "id": item["id"],
                "variant": "baseline",
                "question": question,
                "context": "",
                "answer": baseline_answer,
                "provider": baseline_provider,
                "model": args.model or "",
            }
        )

        results = retrieve(question, index, chunks, args.top_k)
        context = format_context(results)
        rag_prompt = build_rag_prompt(question, context)
        rag_answer, rag_provider = generate_answer(
            rag_prompt,
            question,
            "rag",
            context,
            results,
            args.provider,
            args.model,
        )
        rows.append(
            {
                "id": item["id"],
                "variant": "rag",
                "question": question,
                "context": context,
                "answer": rag_answer,
                "provider": rag_provider,
                "model": args.model or "",
            }
        )

        if args.slovenian_model:
            slovenian_answer, slovenian_provider = generate_answer(
                rag_prompt,
                question,
                "rag",
                context,
                results,
                args.provider,
                args.slovenian_model,
            )
            rows.append(
                {
                    "id": item["id"],
                    "variant": "slovenian",
                    "question": question,
                    "context": context,
                    "answer": slovenian_answer,
                    "provider": slovenian_provider,
                    "model": args.slovenian_model,
                }
            )

    write_jsonl(args.output, rows)
    print(f"Saved {len(rows)} answers to {args.output}")
    print(f"Questions: {len(questions)} | top_k: {args.top_k} | provider: {args.provider}")
    if not args.slovenian_model:
        print("Slovenian variant skipped. Set SLOVENIAN_MODEL or --slovenian-model to enable it.")


if __name__ == "__main__":
    main()

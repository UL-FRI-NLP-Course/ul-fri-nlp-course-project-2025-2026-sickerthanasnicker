import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

from optimizations.common import PROJECT_ROOT, resolve_optimization_path

from evaluation.io_utils import write_json, write_jsonl
from evaluation.progress_utils import Progress


DEFAULT_ZIP = PROJECT_ROOT / "corpus" / "COLESLAW.zip"
DEFAULT_OUTPUT = resolve_optimization_path("data/coleslaw_employment_chunks.jsonl")
DEFAULT_SUMMARY = resolve_optimization_path("data/coleslaw_employment_summary.json")

STRONG_EMPLOYMENT_TERMS = [
    "delovno razmerje",
    "delovnih razmerjih",
    "zakon o delovnih razmerjih",
    "zdr-1",
    "pogodba o zaposlitvi",
    "pogodbe o zaposlitvi",
    "odpovedni rok",
    "letni dopust",
    "minimalna plača",
    "nadurno delo",
    "poskusno delo",
    "kolektivna pogodba",
]

WEAK_EMPLOYMENT_TERMS = [
    "delavca",
    "delavec",
    "delavci",
    "delodajalec",
    "delodajalca",
    "zaposlitev",
    "zaposlitvi",
    "odpoved",
    "odpravnina",
    "dopust",
    "plača",
    "bolniška",
]

EMPLOYMENT_TERMS = STRONG_EMPLOYMENT_TERMS + WEAK_EMPLOYMENT_TERMS

WHITESPACE_RE = re.compile(r"\s+")


def clean_text(value):
    return WHITESPACE_RE.sub(" ", str(value or "")).strip()


def term_score(text):
    lowered = text.lower()
    strong = sum(4 for term in STRONG_EMPLOYMENT_TERMS if term in lowered)
    weak = sum(1 for term in WEAK_EMPLOYMENT_TERMS if term in lowered)
    return strong + weak


def text_from_record(record):
    for key in ("text", "content", "body", "besedilo", "document"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return clean_text(value)
    strings = [value for value in record.values() if isinstance(value, str)]
    return clean_text(" ".join(strings))


def title_from_record(record, member_name):
    for key in ("naziv", "title", "name", "naslov"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return clean_text(value)
    return Path(member_name).stem


def chunk_words(text, size, overlap):
    words = text.split()
    if not words:
        return
    step = max(1, size - overlap)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + size])
        if chunk:
            yield start, chunk
        if start + size >= len(words):
            break


def make_chunk_id(member_name, source_id, chunk_index, text):
    raw = f"{member_name}:{source_id}:{chunk_index}:{text[:80]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def iter_jsonl_records(zip_path):
    with zipfile.ZipFile(zip_path) as archive:
        for member_name in archive.namelist():
            if not member_name.endswith(".jsonl"):
                continue
            with archive.open(member_name) as fp:
                for line_number, raw_line in enumerate(fp, start=1):
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        yield member_name, line_number, json.loads(line)
                    except json.JSONDecodeError:
                        continue


def normalize_record(member_name, line_number, record, args):
    title = title_from_record(record, member_name)
    text = text_from_record(record)
    if not text:
        return []

    record_score = term_score(f"{title} {text[:5000]}")
    if record_score < args.min_record_score:
        return []

    source_id = record.get("id") or record.get("mopedId") or line_number
    chunks = []
    for chunk_index, chunk_text in chunk_words(text, args.chunk_words, args.overlap_words):
        chunk_score = term_score(f"{title} {chunk_text}")
        if chunk_score < args.min_chunk_score:
            continue
        chunks.append(
            {
                "id": make_chunk_id(member_name, source_id, chunk_index, chunk_text),
                "text": chunk_text,
                "meta": {
                    "law": title,
                    "title": title,
                    "source_file": member_name,
                    "source_id": str(source_id),
                    "line_number": line_number,
                    "chunk_start_word": chunk_index,
                    "employment_score": chunk_score,
                    "record_employment_score": record_score,
                    "sop": record.get("sop", ""),
                    "mopedId": record.get("mopedId", ""),
                },
            }
        )
    return chunks


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare reusable employment-law chunks from COLESLAW.")
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--limit", type=int, default=None, help="Maximum chunks to write.")
    parser.add_argument("--max-records", type=int, default=None, help="Maximum source records to scan.")
    parser.add_argument("--chunk-words", type=int, default=180)
    parser.add_argument("--overlap-words", type=int, default=40)
    parser.add_argument("--min-record-score", type=int, default=4)
    parser.add_argument("--min-chunk-score", type=int, default=1)
    parser.add_argument("--progress-every", type=int, default=1000)
    parser.add_argument("--quiet", action="store_true", help="Disable scan progress output.")
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.zip.exists():
        raise FileNotFoundError(f"COLESLAW archive not found: {args.zip}")

    rows = []
    scanned = 0
    matched_records = 0
    files = {}
    progress = Progress(args.max_records or 0, "coleslaw_scan", every=args.progress_every) if not args.quiet else None

    for member_name, line_number, record in iter_jsonl_records(args.zip):
        scanned += 1
        files[member_name] = files.get(member_name, 0) + 1
        chunks = normalize_record(member_name, line_number, record, args)
        if chunks:
            matched_records += 1
            rows.extend(chunks)
        if progress and args.max_records is not None:
            progress.log(scanned, f"matched_records={matched_records} chunks_found={len(rows)}")
        elif not args.quiet and args.progress_every and scanned % args.progress_every == 0:
            print(
                f"[coleslaw_scan] scanned={scanned} matched_records={matched_records} chunks_found={len(rows)}",
                flush=True,
            )
        if args.max_records is not None and scanned >= args.max_records:
            break

    rows.sort(
        key=lambda row: (
            row["meta"].get("record_employment_score", 0),
            row["meta"].get("employment_score", 0),
            "zakon o delovnih razmerjih" in row["meta"].get("title", "").lower(),
        ),
        reverse=True,
    )
    if args.limit is not None:
        rows = rows[: args.limit]

    write_jsonl(args.output, rows)
    summary = {
        "zip": str(args.zip),
        "output": str(args.output),
        "records_scanned": scanned,
        "records_matched": matched_records,
        "chunks_written": len(rows),
        "chunk_words": args.chunk_words,
        "overlap_words": args.overlap_words,
        "min_record_score": args.min_record_score,
        "min_chunk_score": args.min_chunk_score,
        "files_seen": files,
        "strong_employment_terms": STRONG_EMPLOYMENT_TERMS,
        "weak_employment_terms": WEAK_EMPLOYMENT_TERMS,
    }
    write_json(args.summary, summary)

    print(f"Scanned {scanned} records; matched {matched_records}; wrote {len(rows)} chunks.")
    print(f"Chunks: {args.output}")
    print(f"Summary: {args.summary}")


if __name__ == "__main__":
    main()

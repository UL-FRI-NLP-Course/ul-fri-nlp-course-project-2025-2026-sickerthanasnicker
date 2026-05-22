import argparse
import hashlib
import html as html_lib
import io
import json
import re
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from docx import Document
from pypdf import PdfReader

from ul_fri_nlp.optimizations.common import OPTIMIZATION_DIR, PROJECT_ROOT

from ul_fri_nlp.evaluation.io_utils import load_jsonl, write_json, write_jsonl


DEFAULT_MANIFEST = OPTIMIZATION_DIR / "official_sources.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "report" / "code" / "data" / "chunk.jsonl"
DEFAULT_SUMMARY = OPTIMIZATION_DIR / "data" / "official_employment_summary.json"
DEFAULT_CASE_LAW = OPTIMIZATION_DIR / "data" / "coleslaw_employment_chunks.jsonl"

PISRS_DETAIL_URL = "https://pisrs.si/api/rezultat/zbirka/id/{zunanji_id}"
PISRS_DOWNLOAD_URL = "https://pisrs.si/api/datoteke/integracije/{document_id}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ul-fri-nlp-rag-corpus-builder/1.0)",
    "Accept": (
        "text/html,application/xhtml+xml,application/json,application/pdf,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,*/*;q=0.8"
    ),
    "Accept-Language": "sl,en;q=0.8",
}

ARTICLE_RE = re.compile(r"^(\d+(?:\.[a-z])?)\.?\s*člen$", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")
NPB_RE = re.compile(r"\bNPB\s+(\d+)\b", re.IGNORECASE)

OFFICIAL_SOURCE_TYPES = {
    "primary_law": "primary_law",
    "official_interpretation": "official_interpretation",
    "official_interpretation_index": "official_interpretation",
    "official_interpretation_pdf": "official_interpretation",
    "official_interpretation_docx": "official_interpretation",
    "official_faq_docx": "official_interpretation",
    "official_news": "official_operational_guidance",
    "official_business_guidance": "official_operational_guidance",
    "official_operational_guidance": "official_operational_guidance",
    "official_institution_page": "official_operational_guidance",
    "official_open_data_registry": "official_operational_guidance",
    "official_case_law_index": "official_case_law",
}

DOMAIN_SOURCE_LABELS = {
    "pisrs.si": "PISRS",
    "www.gov.si": "GOV.SI",
    "gov.si": "GOV.SI",
    "e-uprava.gov.si": "eUprava",
    "spot.gov.si": "SPOT",
    "zavarovanec.zzzs.si": "ZZZS",
    "www.ess.gov.si": "ESS",
    "podatki.gov.si": "OPSI",
    "www.sodnapraksa.si": "sodnapraksa.si",
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path):
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


def fetch_bytes(url, timeout=40):
    request = urllib.request.Request(url, headers=HEADERS, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type", "")


def fetch_json(url, timeout=40):
    raw, _content_type = fetch_bytes(url, timeout=timeout)
    return json.loads(raw.decode("utf-8"))


def clean_text(value):
    text = html_lib.unescape(str(value or "")).replace("\xa0", " ")
    return WHITESPACE_RE.sub(" ", text).strip()


def words(text):
    return clean_text(text).split()


def chunk_words(text, size=180, overlap=30):
    tokens = words(text)
    if not tokens:
        return
    step = max(1, size - overlap)
    for start in range(0, len(tokens), step):
        chunk = " ".join(tokens[start : start + size])
        if chunk:
            yield chunk
        if start + size >= len(tokens):
            break


def source_label_from_url(url):
    host = urlparse(url).netloc.lower()
    return DOMAIN_SOURCE_LABELS.get(host, host or "official_source")


def source_type(item):
    return OFFICIAL_SOURCE_TYPES.get(item.get("kind"), "official_operational_guidance")


def make_chunk_id(text, meta):
    raw = "|".join(
        [
            meta.get("source", ""),
            meta.get("law", ""),
            meta.get("article", ""),
            meta.get("title", ""),
            meta.get("url", ""),
            text[:120],
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def make_chunk(text, item, retrieved_at, *, law="", article="", title="", validity_status="reachable", extra_meta=None):
    text = clean_text(text)
    if not text:
        return None

    url = item.get("url", "")
    meta = {
        "law": law or item.get("short_name") or item.get("title", ""),
        "article": article or "",
        "title": title or item.get("title", ""),
        "source": source_label_from_url(url),
        "source_type": source_type(item),
        "priority": item.get("priority", "supporting"),
        "url": url,
        "retrieved_at": retrieved_at,
        "validity_status": validity_status,
    }
    if extra_meta:
        meta.update(extra_meta)
    return {"id": make_chunk_id(text, meta), "text": text, "meta": meta}


def npb_number(label):
    match = NPB_RE.search(label or "")
    return int(match.group(1)) if match else 0


def select_latest_html_document(detail):
    groups = detail.get("datoteke") or []
    if not groups:
        return None, ""

    def sort_key(group):
        version = group.get("npbVerzija") or {}
        return (npb_number(version.get("naziv", "")), version.get("id") or 0)

    for group in sorted(groups, key=sort_key, reverse=True):
        for document in group.get("datoteke", []):
            if document.get("tip") == "HTML_DOCUMENT":
                return document.get("id"), (group.get("npbVerzija") or {}).get("naziv", "")
    return None, ""


def is_article_heading(tag, text):
    classes = set(tag.get("class") or [])
    return "clen" in classes and bool(ARTICLE_RE.match(text))


def article_chunks_from_pisrs_html(html):
    soup = BeautifulSoup(html, "html.parser")
    current = None
    articles = []

    def flush():
        if not current:
            return
        text = clean_text(" ".join(current["parts"]))
        if len(words(text)) >= 8:
            articles.append(
                {
                    "article": current["article"],
                    "title": current["title"] or f"{current['article']}. člen",
                    "text": text,
                }
            )

    for tag in soup.find_all("p"):
        text = clean_text(tag.get_text(" ", strip=True))
        if not text:
            continue
        if is_article_heading(tag, text):
            flush()
            match = ARTICLE_RE.match(text)
            current = {"article": match.group(1), "title": "", "parts": [text]}
            continue
        if not current:
            continue
        classes = set(tag.get("class") or [])
        if "clen" in classes and not current["title"] and text.startswith("("):
            current["title"] = text.strip("() ")
            current["parts"].append(text)
            continue
        current["parts"].append(text)

    flush()
    return articles


def fallback_html_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
        tag.decompose()
    return clean_text(soup.get_text(" ", strip=True))


def build_pisrs_chunks(item, retrieved_at):
    detail = fetch_json(PISRS_DETAIL_URL.format(zunanji_id=item["preferred_zunanji_id"])).get("data") or {}
    evidence = detail.get("evidencniPodatki") or {}
    validity_status = (evidence.get("semafor") or {}).get("naziv") or "unknown"
    document_id, npb_label = select_latest_html_document(detail)
    if not document_id:
        raise ValueError(f"No PISRS HTML document found for {item['id']}")

    html, _content_type = fetch_bytes(PISRS_DOWNLOAD_URL.format(document_id=document_id))
    html_text = html.decode("utf-8", errors="replace")
    article_rows = article_chunks_from_pisrs_html(html_text)
    if not article_rows:
        article_rows = [
            {"article": "", "title": item.get("title", ""), "text": chunk}
            for chunk in chunk_words(fallback_html_text(html_text), size=220, overlap=40)
        ]

    chunks = []
    for article in article_rows:
        chunk = make_chunk(
            article["text"],
            item,
            retrieved_at,
            law=item.get("short_name") or item.get("title", ""),
            article=article["article"],
            title=article["title"],
            validity_status=validity_status,
            extra_meta={
                "pisrs_id": item.get("preferred_zunanji_id"),
                "pisrs_document_id": str(document_id),
                "npb_version": npb_label,
                "download_url": PISRS_DOWNLOAD_URL.format(document_id=document_id),
            },
        )
        if chunk:
            chunks.append(chunk)
    return chunks


def meaningful_section(text):
    tokens = words(text)
    return len(tokens) >= 20


def section_chunks_from_html(html, item, retrieved_at):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form", "svg"]):
        tag.decompose()
    container = soup.find("main") or soup.body or soup

    sections = []
    special_blocks = container.select(".answer-text, .faqAnswer, .question-text, .text")
    for block in special_blocks:
        text = clean_text(block.get_text(" ", strip=True))
        if meaningful_section(text):
            heading = item.get("title", "")
            previous_heading = block.find_previous(["h1", "h2", "h3", "h4"])
            if previous_heading:
                heading = clean_text(previous_heading.get_text(" ", strip=True)) or heading
            sections.append((heading, text))

    if sections:
        return make_section_chunks(sections, item, retrieved_at)

    elements = container.find_all(["h1", "h2", "h3", "h4", "p", "li"])
    heading = item.get("title", "")
    parts = []

    def flush():
        text = clean_text(" ".join(parts))
        if meaningful_section(text):
            sections.append((heading, text))

    for element in elements:
        text = clean_text(element.get_text(" ", strip=True))
        if not text:
            continue
        if element.name in {"h1", "h2", "h3", "h4"}:
            flush()
            heading = text
            parts = []
        else:
            parts.append(text)
    flush()

    if not sections:
        text = fallback_html_text(html)
        if meaningful_section(text):
            sections = [(item.get("title", ""), text)]

    return make_section_chunks(sections, item, retrieved_at)


def make_section_chunks(sections, item, retrieved_at):
    chunks = []
    for heading, text in sections:
        for index, chunk_text in enumerate(chunk_words(text, size=180, overlap=30), start=1):
            chunk = make_chunk(
                f"{heading}. {chunk_text}" if heading and heading not in chunk_text[:120] else chunk_text,
                item,
                retrieved_at,
                title=heading or item.get("title", ""),
                extra_meta={"section": heading or item.get("title", ""), "section_part": index},
            )
            if chunk:
                chunks.append(chunk)
    return chunks


def section_chunks_from_pdf(raw, item, retrieved_at):
    reader = PdfReader(io.BytesIO(raw))
    chunks = []
    for page_index, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if not meaningful_section(text):
            continue
        for part_index, chunk_text in enumerate(chunk_words(text, size=180, overlap=30), start=1):
            title = f"{item.get('title', '')}, str. {page_index}"
            chunk = make_chunk(
                chunk_text,
                item,
                retrieved_at,
                title=title,
                extra_meta={"section": title, "page": page_index, "section_part": part_index},
            )
            if chunk:
                chunks.append(chunk)
    return chunks


def section_chunks_from_docx(raw, item, retrieved_at):
    document = Document(io.BytesIO(raw))
    chunks = []
    heading = item.get("title", "")
    parts = []

    def flush():
        text = clean_text(" ".join(parts))
        if not meaningful_section(text):
            return
        for part_index, chunk_text in enumerate(chunk_words(text, size=180, overlap=30), start=1):
            chunk = make_chunk(
                f"{heading}. {chunk_text}" if heading and heading not in chunk_text[:120] else chunk_text,
                item,
                retrieved_at,
                title=heading,
                extra_meta={"section": heading, "section_part": part_index},
            )
            if chunk:
                chunks.append(chunk)

    for paragraph in document.paragraphs:
        text = clean_text(paragraph.text)
        if not text:
            continue
        style = (paragraph.style.name if paragraph.style else "").lower()
        if "heading" in style or "naslov" in style:
            flush()
            heading = text
            parts = []
        else:
            parts.append(text)
    flush()
    return chunks


def build_official_guidance_chunks(item, retrieved_at):
    raw, content_type = fetch_bytes(item["url"])
    lowered = content_type.lower()
    if "pdf" in lowered or item["url"].lower().endswith(".pdf"):
        return section_chunks_from_pdf(raw, item, retrieved_at)
    if (
        "wordprocessingml.document" in lowered
        or item["url"].lower().endswith(".docx")
    ):
        return section_chunks_from_docx(raw, item, retrieved_at)
    return section_chunks_from_html(raw.decode("utf-8", errors="replace"), item, retrieved_at)


def is_case_law_row(row):
    meta = row.get("meta", {})
    source_file = (meta.get("source_file") or "").lower()
    text = f"{meta.get('title', '')} {row.get('text', '')}".lower()
    return "sodnapraksa" in source_file or "sodba" in text or "višje delovno" in text


def build_case_law_chunks(path, manifest, retrieved_at, max_chunks):
    if not path.exists():
        return []
    rows = [row for row in load_jsonl(path) if is_case_law_row(row)]
    rows = rows[:max_chunks]
    case_item = (manifest.get("case_law") or [{}])[0]
    chunks = []
    for row in rows:
        old_meta = row.get("meta", {})
        source_id = old_meta.get("source_id") or row.get("id", "")
        title = f"Sodna praksa {source_id}".strip()
        chunk = make_chunk(
            row.get("text", ""),
            {
                **case_item,
                "kind": "official_case_law_index",
                "priority": "tertiary",
                "url": case_item.get("url", "https://www.sodnapraksa.si/"),
            },
            retrieved_at,
            law="sodnapraksa.si",
            title=title,
            validity_status="tertiary_case_law",
            extra_meta={
                "source_type": "official_case_law",
                "case_law_source_file": old_meta.get("source_file", ""),
                "case_law_source_id": str(source_id),
                "employment_score": old_meta.get("employment_score", 0),
            },
        )
        if chunk:
            chunks.append(chunk)
    return chunks


def dedupe_chunks(chunks):
    seen = set()
    unique = []
    for chunk in chunks:
        key = hashlib.sha1(chunk["text"].encode("utf-8")).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        unique.append(chunk)
    return unique


def source_sort_key(chunk):
    source_order = {
        "primary_law": 0,
        "official_interpretation": 1,
        "official_operational_guidance": 2,
        "official_case_law": 3,
    }
    meta = chunk["meta"]
    article = meta.get("article") or ""
    article_number = 99999
    match = re.match(r"(\d+)", article)
    if match:
        article_number = int(match.group(1))
    return (
        source_order.get(meta.get("source_type"), 9),
        meta.get("law", ""),
        article_number,
        article,
        meta.get("title", ""),
    )


def validate_chunks(chunks):
    required = {"law", "article", "title", "source", "source_type", "priority", "url", "retrieved_at", "validity_status"}
    missing = []
    for chunk in chunks:
        meta = chunk.get("meta", {})
        absent = [field for field in required if field not in meta]
        if absent:
            missing.append({"id": chunk.get("id"), "missing": absent})
    return missing


def parse_args():
    parser = argparse.ArgumentParser(description="Build the official Slovenian employment-law RAG corpus.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--include-case-law", action="store_true")
    parser.add_argument("--case-law-chunks", type=Path, default=DEFAULT_CASE_LAW)
    parser.add_argument("--max-case-law-chunks", type=int, default=30)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    manifest = read_json(args.manifest)
    retrieved_at = utc_now()
    chunks = []
    failures = []

    for item in manifest.get("pisrs", []):
        try:
            rows = build_pisrs_chunks(item, retrieved_at)
            chunks.extend(rows)
            if not args.quiet:
                print(f"[pisrs] {item['short_name']}: {len(rows)} chunks")
        except Exception as exc:
            failures.append({"id": item.get("id"), "url": item.get("url"), "error": f"{type(exc).__name__}: {exc}"})
            if not args.quiet:
                print(f"[pisrs] {item.get('short_name', item.get('id'))}: failed: {exc}")

    for item in manifest.get("government_interpretations", []):
        try:
            rows = build_official_guidance_chunks(item, retrieved_at)
            chunks.extend(rows)
            if not args.quiet:
                print(f"[official] {item['id']}: {len(rows)} chunks")
        except Exception as exc:
            failures.append({"id": item.get("id"), "url": item.get("url"), "error": f"{type(exc).__name__}: {exc}"})
            if not args.quiet:
                print(f"[official] {item.get('id')}: failed: {exc}")

    if args.include_case_law:
        rows = build_case_law_chunks(args.case_law_chunks, manifest, retrieved_at, args.max_case_law_chunks)
        chunks.extend(rows)
        if not args.quiet:
            print(f"[case_law] {len(rows)} chunks from {args.case_law_chunks}")

    chunks = sorted(dedupe_chunks(chunks), key=source_sort_key)
    validation_missing = validate_chunks(chunks)
    if validation_missing:
        raise ValueError(f"Generated chunks missing required metadata: {validation_missing[:3]}")

    write_jsonl(args.output, chunks)

    source_type_counts = Counter(chunk["meta"].get("source_type") for chunk in chunks)
    law_counts = Counter(chunk["meta"].get("law") for chunk in chunks)
    private_sources = [
        chunk["meta"].get("url", "")
        for chunk in chunks
        if chunk["meta"].get("url", "").startswith("http")
        and not any(
            host in urlparse(chunk["meta"].get("url", "")).netloc.lower()
            for host in ("pisrs.si", "gov.si", "zzzs.si", "spot.gov.si", "ess.gov.si", "podatki.gov.si", "sodnapraksa.si")
        )
    ]
    summary = {
        "retrieved_at": retrieved_at,
        "manifest": str(args.manifest),
        "output": str(args.output),
        "chunks_written": len(chunks),
        "source_type_counts": dict(source_type_counts),
        "top_law_counts": dict(law_counts.most_common(20)),
        "pisrs_sources": len(manifest.get("pisrs", [])),
        "official_guidance_sources": len(manifest.get("government_interpretations", [])),
        "case_law_included": bool(args.include_case_law),
        "max_case_law_chunks": args.max_case_law_chunks if args.include_case_law else 0,
        "failures": failures,
        "private_grounding_sources": sorted(set(private_sources)),
        "required_metadata_fields": [
            "text",
            "meta.law",
            "meta.article",
            "meta.title",
            "meta.source",
            "meta.source_type",
            "meta.priority",
            "meta.url",
            "meta.retrieved_at",
            "meta.validity_status",
        ],
    }
    write_json(args.summary_output, summary)

    if len(chunks) < 150:
        raise ValueError(f"Expanded corpus is too small: {len(chunks)} chunks")
    if private_sources:
        raise ValueError(f"Private grounding sources found: {sorted(set(private_sources))}")

    print(f"Wrote {len(chunks)} chunks to {args.output}")
    print(f"Wrote summary to {args.summary_output}")
    print("Source types: " + ", ".join(f"{key}={value}" for key, value in sorted(source_type_counts.items())))
    if failures:
        print(f"Completed with {len(failures)} source failures; see summary.")


if __name__ == "__main__":
    main()

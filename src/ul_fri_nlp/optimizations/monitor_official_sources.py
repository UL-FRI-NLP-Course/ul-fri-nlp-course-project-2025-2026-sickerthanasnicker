import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ul_fri_nlp.optimizations.common import OPTIMIZATION_DIR, PROJECT_ROOT

from ul_fri_nlp.evaluation.io_utils import write_json


DEFAULT_MANIFEST = OPTIMIZATION_DIR / "official_sources.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "evaluation" / "results" / "optimization" / "official_source_monitor.json"
PISRS_FILTER_URL = "https://pisrs.si/api/filter/filter"
SOURCE_MONITOR_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ul-fri-nlp-rag-source-monitor/1.0; "
        "+https://fri.uni-lj.si/)"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/pdf,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,*/*;q=0.8"
    ),
    "Accept-Language": "sl,en;q=0.8",
    "Cache-Control": "no-cache",
}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path):
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


def json_request(url, payload, timeout=30):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "User-Agent": "ul-fri-nlp-rag-source-monitor/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def source_status(url, timeout=20):
    last_error = None
    for method in ("HEAD", "GET"):
        for attempt in range(2):
            request = urllib.request.Request(url, headers=SOURCE_MONITOR_HEADERS, method=method)
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return {
                        "ok": 200 <= response.status < 400,
                        "status": response.status,
                        "content_type": response.headers.get("Content-Type", ""),
                        "last_modified": response.headers.get("Last-Modified", ""),
                    }
            except urllib.error.HTTPError as exc:
                last_error = {
                    "ok": False,
                    "status": exc.code,
                    "content_type": exc.headers.get("Content-Type", "") if exc.headers else "",
                    "last_modified": exc.headers.get("Last-Modified", "") if exc.headers else "",
                    "error": str(exc),
                }
                if method == "HEAD" and exc.code in {403, 405, 429, 500, 502, 503, 504}:
                    break
                if exc.code in {429, 500, 502, 503, 504} and attempt == 0:
                    time.sleep(0.5)
                    continue
                return last_error
            except Exception as exc:
                last_error = {"ok": False, "status": None, "error": f"{type(exc).__name__}: {exc}"}
                if method == "HEAD":
                    break
                if attempt == 0:
                    time.sleep(0.5)
                    continue
                return last_error
    return last_error or {"ok": False, "status": None, "error": "No HTTP response."}


def pisrs_payload(source, collections):
    return {
        "simpleSearch": True,
        "besedilo": {
            "word1": source["query"],
            "word1InTitle": True,
            "word1InContent": True,
            "word2": None,
            "word2InTitle": False,
            "word2InContent": False,
            "filterQualifier": "AND",
        },
        "nazivZbirke": collections,
    }


def pisrs_item_url(item):
    zunanji_id = item.get("zunanjiId")
    if not zunanji_id:
        return ""
    if item.get("nazivZbirke") == "Neuradna prečiščena besedila" and item.get("izvorniPredpisMopedId"):
        params = urllib.parse.urlencode(
            {
                "idPredpisa": zunanji_id,
                "idPredpisaChng": item["izvorniPredpisMopedId"],
            }
        )
        return f"https://pisrs.si/Pis.web/pregledNpb?{params}"
    return f"https://pisrs.si/Pis.web/pregledPredpisa?id={urllib.parse.quote(str(zunanji_id))}"


def normalize_pisrs_item(item):
    semafor = item.get("semafor") or {}
    return {
        "naziv_akta": item.get("nazivAkta"),
        "zunanji_id": item.get("zunanjiId"),
        "interni_id": item.get("interniId"),
        "zbirka": item.get("nazivZbirke"),
        "sop": item.get("sop"),
        "datum_objave": item.get("datumObjave"),
        "datum_sprejetja": item.get("datumSprejetja"),
        "st_npb": item.get("stNpb"),
        "izvorni_predpis_moped_id": item.get("izvorniPredpisMopedId"),
        "status": semafor.get("naziv"),
        "url": pisrs_item_url(item),
    }


def npb_sort_key(item):
    st_npb = item.get("stNpb")
    try:
        st_npb = int(st_npb)
    except (TypeError, ValueError):
        st_npb = -1
    return (st_npb, item.get("datumObjave") or "")


def select_pisrs_matches(items, preferred_id):
    exact = [item for item in items if item.get("zunanjiId") == preferred_id]
    register = [item for item in exact if item.get("nazivZbirke") == "Register predpisov"]
    npb = [item for item in exact if item.get("nazivZbirke") == "Neuradna prečiščena besedila"]
    latest_npb = max(npb, key=npb_sort_key) if npb else None
    return {
        "register_match": normalize_pisrs_item(register[0]) if register else None,
        "latest_npb_match": normalize_pisrs_item(latest_npb) if latest_npb else None,
        "top_results": [normalize_pisrs_item(item) for item in items[:5]],
        "exact_result_count": len(exact),
    }


def monitor_pisrs_source(source, collections):
    payload = pisrs_payload(source, collections)
    response = json_request(PISRS_FILTER_URL, payload)
    data = response.get("data", {})
    items = data.get("seznam") or []
    matches = select_pisrs_matches(items, source.get("preferred_zunanji_id"))
    register = matches["register_match"]
    status_ok = bool(register and register.get("status") == "Veljaven predpis")
    return {
        "id": source["id"],
        "short_name": source.get("short_name"),
        "title": source.get("title"),
        "query": source["query"],
        "preferred_zunanji_id": source.get("preferred_zunanji_id"),
        "priority": source.get("priority"),
        "kind": source.get("kind"),
        "status_ok": status_ok,
        "result_count_cursor": data.get("numOfResultsForCursor"),
        "result_count_total": data.get("numOfAllResultsForIndex"),
        **matches,
    }


def monitor_url_group(items):
    rows = []
    for item in items:
        status = source_status(item["url"])
        rows.append(
            {
                "id": item["id"],
                "title": item.get("title"),
                "url": item["url"],
                "owner": item.get("owner"),
                "kind": item.get("kind"),
                "priority": item.get("priority"),
                "status_ok": status.get("ok", False),
                "http": status,
            }
        )
    return rows


def parse_args():
    parser = argparse.ArgumentParser(description="Monitor official Slovenian employment-law corpus sources.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    manifest = load_json(args.manifest)
    collections = manifest.get("pisrs_collections", ["Register predpisov", "Neuradna prečiščena besedila"])

    pisrs_rows = [monitor_pisrs_source(source, collections) for source in manifest.get("pisrs", [])]
    gov_rows = monitor_url_group(manifest.get("government_interpretations", []))
    case_law_rows = monitor_url_group(manifest.get("case_law", []))

    result = {
        "retrieved_at": utc_now(),
        "manifest": str(args.manifest),
        "pisrs_filter_url": PISRS_FILTER_URL,
        "summary": {
            "pisrs_sources": len(pisrs_rows),
            "pisrs_status_ok": sum(1 for row in pisrs_rows if row.get("status_ok")),
            "government_sources": len(gov_rows),
            "government_status_ok": sum(1 for row in gov_rows if row.get("status_ok")),
            "case_law_sources": len(case_law_rows),
            "case_law_status_ok": sum(1 for row in case_law_rows if row.get("status_ok")),
        },
        "pisrs": pisrs_rows,
        "government_interpretations": gov_rows,
        "case_law": case_law_rows,
    }
    write_json(args.output, result)

    if not args.quiet:
        summary = result["summary"]
        print(f"Saved source monitor snapshot: {args.output}")
        print(
            "PISRS ok: "
            f"{summary['pisrs_status_ok']}/{summary['pisrs_sources']} | "
            "government ok: "
            f"{summary['government_status_ok']}/{summary['government_sources']} | "
            "case law ok: "
            f"{summary['case_law_status_ok']}/{summary['case_law_sources']}"
        )


if __name__ == "__main__":
    main()

# RAG Optimization Report

Date: 2026-05-22

## Final Direction

The final project uses RAG over a committed official corpus. Fine-tuning remains exploratory because legal answers must be grounded in current official sources.

The official corpus is built with:

```bash
python evaluation/optimizations/build_official_corpus.py \
  --output report/code/data/chunk.jsonl \
  --include-case-law \
  --max-case-law-chunks 30
```

Current output:

- `1,371` chunks in `report/code/data/chunk.jsonl`.
- `1,059` PISRS article-level chunks.
- `189` official interpretation chunks.
- `93` official operational-guidance chunks.
- `30` tertiary COLESLAW/sodnapraksa case-law chunks.

## Source Policy

Retrieval and prompting use this authority order:

1. `primary_law`: PISRS statutes and latest available NPB text.
2. `official_interpretation`: GOV.SI and MDDSZ interpretations, PDFs, and DOCX guidance.
3. `official_operational_guidance`: ZZZS, eUprava, SPOT, ESS, and OPSI operational pages.
4. `official_case_law`: sodnapraksa/COLESLAW only as tertiary interpretive support.

Case law is suppressed for statutory questions unless the question explicitly asks about practice, courts, or interpretation.

## Current Evaluation

The evaluation set now has 40 questions covering:

- annual leave and regres;
- fixed-term contracts;
- termination and severance;
- sick leave and ZZZS compensation;
- 2026 minimum wage;
- working-time evidence;
- occupational safety;
- wage non-payment;
- collective agreements;
- case-law interpretation;
- ambiguous in-domain questions;
- out-of-scope refusals.

Latest retrieval summary:

| Metric | Result |
| --- | --- |
| Hit@3 | `1.000` |
| False evidence | `0.000` |
| Average context length | `1430.8` words |

Latest offline RAG answer summary:

| Metric | Result |
| --- | --- |
| Correctness | `2.45` |
| Grounding | `4.65` |
| Hallucination | `2.10` |
| Supported citation rate | `0.97` |
| Refusal accuracy | `1.00` |

## Regression Fixes

| ID | Fix |
| --- | --- |
| `q009` | Fixed-term-contract duration now retrieves `ZDR-1, čl. 55` first and cites the two-year limit. |
| `q012` | Updated from the old 20-day wording to the current official 30-working-day / 31st-day ZDR-1 and ZZZS rule. |
| `q014` | Ambiguous leave question now starts with an ambiguity warning and cites `ZDR-1, čl. 159` and `ZDR-1, čl. 161`. |

## Remaining Work

The remaining limitations are answer synthesis and legal validation. A stronger model, semantic reranker, or constrained answer composer could improve multi-article answers. The project still has no qualified legal-expert audit, so it must remain informational and source-grounded rather than legal advice.

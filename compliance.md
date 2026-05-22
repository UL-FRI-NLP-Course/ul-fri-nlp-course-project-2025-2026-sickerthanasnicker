# Compliance Ledger

This ledger maps the UL FRI Natural Language Processing 2025/2026 final-project and peer-review instructions to repository evidence. It is written for manual peer review: the goal is to make the submission easy to inspect, rerun, and challenge.

## Course Requirements Interpreted From Instructions

| Instruction requirement | Repository evidence | Status |
| --- | --- | --- |
| Final project for the Domain-Specific AI Assistant topic: define a strict use case, curate a source of truth, and adapt an LLM with RAG or PEFT. | `README.md`; `report/report.tex`; `report/code/rag.py`; `evaluation/optimizations/config.json`; `evaluation/optimizations/official_sources.json`. The use case is a Slovenian employment-law assistant with official-source grounding, citations, and refusal behavior. | Covered. Final approach is RAG-first; PEFT/fine-tuning utilities are exploratory, not the submitted production claim. |
| Literature / related-work discussion, including knowledge injection trade-offs such as prompting, RAG, fine-tuning, and tools. | `report/report.tex` sections `Related Work` and `System`; `report/report.bib`. | Covered in the report source. |
| Data curation and domain definition with links or included transformed data. | Source manifest: `evaluation/optimizations/official_sources.json`. Corpus builder: `evaluation/optimizations/build_official_corpus.py`. Committed transformed corpus: `report/code/data/chunk.jsonl`. COLESLAW preprocessing: `evaluation/optimizations/prepare_corpus.py`. | Covered. Official/public sources are linked and reproducible; transformed chunks are committed for inspection. |
| If public datasets are available elsewhere, link them; if transformations were performed, include scripts. | `README.md` documents official source policy and COLESLAW handling. `evaluation/optimizations/README.md` documents corpus, source monitor, COLESLAW extraction, and PEFT data preparation. | Covered, with one limitation: the raw `corpus/COLESLAW.zip` archive is not committed and is expected locally only when regenerating COLESLAW-derived chunks. |
| Implement at least one solution and analyze results. | Implemented solution: BM25-style RAG in `report/code/rag.py` and shared evaluation retrieval in `evaluation/retrieval_shared.py`. Results: `evaluation/results/`, `evaluation/results/report.md`, `evaluation/optimizations/rag_optimization_report.md`, and report tables. | Covered. |
| Evaluate retrieval accuracy/relevance and human-centric answer behavior such as factuality, tone, and safe handling of unanswerable queries. | `evaluation/questions.jsonl` has 40 factual, ambiguous, and unanswerable questions. `evaluation/retrieval_eval.py`, `evaluation/run_eval.py`, `evaluation/judge_eval.py`, and `evaluation/visualize_results.py` generate retrieval and answer metrics. | Covered for deterministic peer review. Human/legal expert validation remains a limitation. |
| Report results with sensible measures, readable figures/tables, and comparative tables where possible. | `report/report.tex` contains retrieval, answer, and regression tables. Generated charts and CSVs are in `evaluation/results/`. | Covered. |
| Keep report concise and follow the proposed report template. | `report/report.tex` uses `report/ds_report.cls`; figures/templates are under `report/`. | Covered. |
| Fully reproducible repository with dependencies and simple rerun path. | `requirements.txt`; `Makefile`; `README.md` reviewer checklist. Main command: `make verify`. Component targets: `make retrieval`, `make offline-eval`, `make report`, `make corpus`, `make source-monitor`. | Covered for offline reproduction. Live Ollama/Open WebUI paths are optional and depend on local endpoints/secrets. |
| Include all dependencies/corpora or clear download/access instructions; do not commit secrets. | Python dependencies in `requirements.txt`; optional PEFT dependencies in `evaluation/optimizations/requirements-peft.txt`; endpoint template in `evaluation/config.example.env`; `.env` ignored. | Covered. |
| Repository should be public before peer-review period. | This cannot be proven from files alone. `README.md` states the project is intended for final peer review. | External action required: repository visibility must be public by the course deadline. |
| Peer review: each group reviews assigned same-topic projects and submits scores/feedback through the form by Monday, May 25, 23:59. | No code artifact is required for submitting peer reviews. This ledger is included to help reviewers evaluate this repository quickly. | Outside repository scope. |

## Current Evidence Snapshot

| Artifact | Current evidence |
| --- | --- |
| Corpus | `report/code/data/chunk.jsonl` has 1,371 chunks. `evaluation/optimizations/data/official_employment_summary.json` reports 1,059 `primary_law`, 189 `official_interpretation`, 93 `official_operational_guidance`, and 30 `official_case_law` chunks. |
| Source manifest | `evaluation/optimizations/official_sources.json` lists 12 PISRS sources, 2 PISRS collections, 24 government/official interpretation sources, 1 case-law source, and a retrieval authority policy. |
| Source availability | `evaluation/results/optimization/official_source_monitor.json` reports 12/12 PISRS sources, 24/24 government sources, and 1/1 case-law source reachable in the latest snapshot. |
| Evaluation set | `evaluation/questions.jsonl` has 40 questions covering employment-law facts, ambiguous in-domain questions, and out-of-scope refusals. |
| Fine-tuning artifacts | `evaluation/fine_tuning/data/train.jsonl` has 16 rows and `dev.jsonl` has 4 rows. Optimization PEFT preparation has 176 train rows and 44 dev rows. These are exploratory artifacts only. |
| Generated report PDF | `make report` writes `report/.out/report.pdf`. Report PDFs and LaTeX build artifacts are intentionally ignored by git via `.gitignore` (`/report/.out/`, `/report/*.pdf`, etc.). |

## Exact Current Metrics

From `evaluation/results/retrieval_summary.csv`:

| answerable_hit_rate | unanswerable_false_evidence_rate | average_context_length_words |
| --- | --- | --- |
| 1.0 | 0.0 | 1430.8 |

From `evaluation/results/summary_scores.csv`:

| model_id | variant | n | correctness | grounding | completeness | clarity | hallucination | supported_citation_rate | refusal_accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| offline-llama3:latest | baseline | 40 | 0.5 | 0.125 | 0.5 | 5.0 | 4.125 | 0.0 | 0.0 |
| offline-llama3:latest | rag | 40 | 2.45 | 4.65 | 2.45 | 4.55 | 2.1 | 0.9696969696969697 | 1.0 |
| raw-rag-prompt | raw_rag_prompt | 40 | 1.5 | 5.0 | 1.5 | 3.25 | 0.0 | 0.0 | 1.0 |

Additional optimization snapshot, useful but secondary to the final CSVs above:

| File | Metric snapshot |
| --- | --- |
| `evaluation/results/optimization/optimization_summary.csv` | Offline optimized RAG: n=40, correctness 2.95, grounding 4.825, completeness 2.95, clarity 4.85, hallucination 1.675, supported citation rate 1.0, refusal accuracy 1.0. |
| `evaluation/results/optimization/optimization_retrieval_summary.csv` | answerable hit rate 1.0, unanswerable false evidence rate 0.0, average context length 448.575 words. |

## Reviewer Reproduction Path

Recommended clean-clone check:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make verify
```

What `make verify` checks:

- JSON configuration validity for `evaluation/config.json`, `evaluation/optimizations/config.json`, and `evaluation/optimizations/official_sources.json`.
- Python compile checks for `evaluation/` and `report/code/`.
- Retrieval metrics through `evaluation/retrieval_eval.py`.
- Deterministic offline generation, judging, and chart/report generation.
- LaTeX build into `report/.out/report.pdf`.

Optional checks:

```bash
make source-monitor
make corpus
python evaluation/list_models.py --provider ollama
python evaluation/list_models.py --provider openwebui
```

## Honest Limitations

- No qualified legal-expert audit is included. The assistant is informational and source-grounded, not legal advice.
- The deterministic offline judge is useful for reproducible regression checks, but it is not a substitute for human legal evaluation.
- Retrieval is lexical/BM25-style and CPU-friendly; there is no dense retriever or learned reranker in the final submitted pipeline.
- Live model evaluation and Open WebUI/Ollama deployment depend on local model availability, endpoint configuration, and secrets not committed to git.
- COLESLAW raw data is not committed; only transformation scripts, summaries, and selected derived/tertiary chunks are present.
- Some historical/manual appendix files may contain older context-length snapshots; for final metrics, use `evaluation/results/retrieval_summary.csv` and `evaluation/results/summary_scores.csv`, reproduced above.

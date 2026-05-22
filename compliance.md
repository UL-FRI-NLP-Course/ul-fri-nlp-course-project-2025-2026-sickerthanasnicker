# Compliance Ledger

Updated: 2026-05-22

This ledger maps the UL FRI Natural Language Processing 2025/2026 final-project instructions to repository evidence. It is written for peer reviewers: the goal is to make the submission straightforward to inspect, rerun, and challenge.

## Course Requirements

| Requirement | Repository evidence | Status |
| --- | --- | --- |
| Domain-specific AI assistant: define a strict use case, curate a knowledge base, adapt an LLM with RAG or PEFT | Domain: Slovenian employment-law question answering. RAG pipeline in `src/ul_fri_nlp/app/rag.py`. Official corpus in `report/code/data/chunk.jsonl`. Prompt and model config in `evaluation/optimizations/config.json`. PEFT data prepared as exploratory artifact, not used for the final system. | Covered. |
| Literature review covering knowledge injection trade-offs (prompting, RAG, fine-tuning, tools) | `report/report.tex` Related Work and System sections. `report/report.bib`: Lewis 2020 (RAG), Hu 2021 (LoRA), Schick 2023 (Toolformer), Song 2025 (domain injection survey). | Covered. |
| Data curation and domain definition with linked or included transformed data | Source manifest: `evaluation/optimizations/official_sources.json`. Corpus builder: `src/ul_fri_nlp/optimizations/build_official_corpus.py`. Committed corpus: `report/code/data/chunk.jsonl` (1,371 chunks). COLESLAW preprocessing: `src/ul_fri_nlp/optimizations/prepare_corpus.py`. | Covered. Raw COLESLAW archive not committed; transformation scripts and selected derived chunks are included. |
| Datasets available elsewhere should be linked; transformation scripts included | Official sources linked in `evaluation/optimizations/official_sources.json` (PISRS, GOV.SI, MDDSZ, ZZZS, etc.). COLESLAW cited in `report/report.bib`. All transformation scripts in `src/ul_fri_nlp/optimizations/`. | Covered. |
| Implement at least one solution with analysis | BM25+domain-adjustment RAG in `src/ul_fri_nlp/app/rag.py`. Results in `evaluation/results/`. Optimization analysis in `evaluation/results/optimization/optimization_report.md`. | Covered. |
| Evaluate retrieval accuracy/relevance and human-centric answer quality (factuality, tone, refusal) | 40-question evaluation set `evaluation/questions.jsonl`. Retrieval eval: `src/ul_fri_nlp/evaluation/retrieval_eval.py`. Answer eval: `src/ul_fri_nlp/evaluation/run_eval.py` + `judge_eval.py`. Charts: `visualize_results.py`. | Covered. Expert legal validation is a stated limitation. |
| Report results with sensible measures, readable figures/tables, and comparative tables | Results tables in `report/report.tex`. Generated charts (PNG/SVG/JPG) in `evaluation/results/`. CSV summaries in `evaluation/results/summary_scores.csv` and `retrieval_summary.csv`. | Covered. |
| Keep report concise (≤ 4 pages + references + appendices) and follow the proposed template | `report/report.tex` uses `report/ds_report.cls`. Builds to `report/.out/report.pdf` with `make report`. | Covered. |
| Fully reproducible repository with all dependencies and a simple rerun path | `requirements.txt`, `Makefile`, offline evaluation path, `evaluation/config.example.env`. Main command: `make verify`. | Covered. Live Ollama/Open WebUI paths depend on local endpoints. |
| Do not commit secrets | `.env` ignored by git. Only the endpoint template `evaluation/config.example.env` is committed. `WEBUI_API_KEY`, `OLLAMA_URL`, and similar are never committed. | Covered. |
| Repository public before peer-review deadline | Cannot be verified from files. Repository visibility must be set to public by the course deadline (2026-05-22 23:59). | External action required. |
| Peer review submission by Monday 2026-05-26 23:59 | Outside repository scope. | External obligation. |

---

## Exact Metrics From Committed Files

### Retrieval — `evaluation/results/retrieval_summary.csv`

| Metric | Value |
| --- | --- |
| Answerable hit rate (Hit@3) | 1.000 |
| Unanswerable false-evidence rate | 0.000 |
| Average context length (words) | 1430.8 |

### Answer quality — `evaluation/results/summary_scores.csv`

| model\_id | variant | n | correctness | grounding | completeness | clarity | hallucination | citation\_rate | refusal\_accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| offline-llama3:latest | baseline | 40 | 0.50 | 0.12 | 0.50 | 5.00 | 4.12 | 0.00 | 0.00 |
| offline-llama3:latest | rag | 40 | 2.45 | 4.65 | 2.45 | 4.55 | 2.10 | 0.97 | 1.00 |
| raw-rag-prompt | raw\_rag\_prompt | 40 | 1.50 | 5.00 | 1.50 | 3.25 | 0.00 | 0.00 | 1.00 |

### Optimized system — `evaluation/results/optimization/optimization_summary.csv`

Using `strict_legal_rag_sl_v3` prompt + deterministic settings on mistral:7b:

| model\_id | variant | n | correctness | grounding | completeness | clarity | hallucination | citation\_rate | refusal\_accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| offline-webui-mistral-7b | baseline | 40 | 0.50 | 0.12 | 0.50 | 5.00 | 4.12 | 0.00 | 0.00 |
| offline-webui-mistral-7b | rag | 40 | 2.95 | 4.83 | 2.95 | 4.85 | 1.68 | 1.00 | 1.00 |

### Corpus — `evaluation/optimizations/data/official_employment_summary.json`

| Source type | Chunks |
| --- | ---: |
| primary\_law | 1059 |
| official\_interpretation | 189 |
| official\_operational\_guidance | 93 |
| official\_case\_law | 30 |
| **Total** | **1371** |

### Source monitor — `evaluation/results/optimization/official_source_monitor.json`

| Category | Status |
| --- | --- |
| PISRS sources | 12/12 reachable |
| Government/official sources | 24/24 reachable |
| Case-law index | 1/1 reachable |

---

## Corpus Rebuild and Reproducibility Path

Recommended clean-clone check:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make verify
```

`make verify` runs: JSON config validation, Python compile check, retrieval metrics, offline generation/judge/charts pipeline, LaTeX report build.

Optional checks:

```bash
make source-monitor      # check official source availability
make corpus              # rebuild report/code/data/chunk.jsonl from official sources
```

---

## Report Narrative Verification

This subsection provides evidence for the specific claims made in `report/report.tex` and `README.md`. Each row maps a report claim to a verifiable repository artifact.

| Report claim | Verification artifact | Confirmed? |
| --- | --- | --- |
| "1,371 chunks: 1,059 PISRS article-level chunks, 189 official interpretation chunks, 93 official operational-guidance chunks, and 30 tertiary COLESLAW/sodnapraksa case-law chunks" | `evaluation/optimizations/data/official_employment_summary.json` — exact counts per source type | Yes |
| "current setup reaches 1.000 answerable Hit@3 with 0.000 false-evidence rate" | `evaluation/results/retrieval_summary.csv` row: `answerable_hit_rate=1.0`, `unanswerable_false_evidence_rate=0.0` | Yes |
| "offline RAG answers preserve high citation support while refusing unsupported questions" | `evaluation/results/summary_scores.csv`: RAG `supported_citation_rate=0.97`, `refusal_accuracy=1.00` | Yes |
| "source monitor currently checks 12 PISRS sources, 24 government or official interpretation/operational sources, and one official case-law index; the latest run found all reachable" | `evaluation/results/optimization/official_source_monitor.json` | Yes |
| "Five prompt iterations … strict_legal_rag_sl_v3" | `evaluation/optimizations/config.json` lists all five prompts with full system text | Yes |
| "BM25 with a simple lexical fallback" | `src/ul_fri_nlp/app/rag.py`: `make_index()` tries `rank_bm25.BM25Okapi`, falls back to `SimpleLexicalIndex` | Yes |
| "source priority: primary_law +7.0, official_interpretation +2.5, official_operational_guidance +2.0" | `src/ul_fri_nlp/app/rag.py`: `SOURCE_TYPE_BONUS` dict | Yes |
| "case-law chunks are suppressed for statutory questions unless the question asks about practice, courts, or interpretation" | `src/ul_fri_nlp/app/rag.py`: `source_priority_adjustment()` — `official_case_law` gets −100 unless `asks_case_law` | Yes |
| "optimized system: correctness 2.95, hallucination 1.68, citation rate 1.00, refusal accuracy 1.00" | `evaluation/results/optimization/optimization_summary.csv`: `rag` row values exactly match | Yes |
| "Deployed at <https://ai.koderverse.com/> as ul-fri-slovenian-employment-law-rag-openwebui" | `evaluation/optimizations/config.json` `webui_export.model_id`; `.env` `OPENWEBUI_URL=https://ai.koderverse.com/` | Yes |
| "three regression failures fixed: q009, q012, q014" | `evaluation/optimizations/rag_optimization_report.md` regression table; `evaluation/manual_eval_appendix.md` Known Failure Fixes table | Yes |
| "Fine-tuning data prepared but not used for the final system" | `evaluation/optimizations/data/peft_train.jsonl` (176 rows), `peft_dev.jsonl` (44 rows); `evaluation/fine_tuning/data/README.md` explicitly marks these exploratory | Yes |
| "GaMS-1B-Chat is the preferred CPU-friendly Slovenian model" | `evaluation/optimizations/config.json` `recommended_model.primary_cpu_candidate = "cjvt/GaMS-1B-Chat"`; `role = "recommended_cpu_slovenian_candidate"` | Yes |
| "arena smoke: all models score 5.00/5 correctness and grounding with RAG on 5-question set" | `evaluation/results/arena_live_smoke_charts/report.md` — all RAG rows show 5.00 correctness and grounding | Yes |

---

## Honest Limitations

- No qualified legal-expert audit is included. The assistant is informational and source-grounded, not certified legal advice.
- The deterministic offline judge is a reproducibility proxy, not a human legal evaluation.
- Retrieval is lexical BM25; no dense embeddings or learned reranker in the final submitted pipeline.
- Live Ollama/Open WebUI evaluation depends on local endpoint availability and secrets not committed to git.
- Raw COLESLAW archive not committed; only transformation scripts, summaries, and selected derived chunks are included.
- For final authoritative metrics, use `evaluation/results/retrieval_summary.csv` and `evaluation/results/summary_scores.csv`. Some older snapshots in manual appendix files may reflect earlier corpus or question-set sizes.

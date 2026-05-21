# Compliance With NLP 2026 Project Instructions

Date: 2026-05-21

This file maps the course instructions in `instructions/Natural language processing 2026.pdf` to the repository evidence for the final Slovenian employment-law RAG assistant.

## Final Status Summary

| Area | Status | Evidence | Notes / deviation |
| --- | --- | --- | --- |
| Final solution | Complete | `report/code/rag.py`, `evaluation/`, `evaluation/optimizations/config.json` | Final solution is RAG-only with strict v3 prompt, lightweight lexical reranking, and official-source monitoring. |
| Final report | Complete | `report/report.tex` | Rewritten as final report; no placeholder abstract or initial-report wording remains. |
| Reproducible repository | Complete | `README.md`, `requirements.txt`, `evaluation/README.md` | Live LLM calls were verified through remote Ollama/Open WebUI aliases; offline smoke mode remains available. |
| Corpus and source curation | Complete | `report/code/data/chunk.jsonl`, `evaluation/optimizations/official_sources.json` | Official source manifest uses PISRS, GOV.SI, MDDSZ, IRSD, eUprava, SPOT, ESS, OPSI, and sodnapraksa.si. |
| Evaluation | Complete | `evaluation/questions.jsonl`, `evaluation/results/`, `evaluation/manual_eval_appendix.md`, `evaluation/optimizations/rag_optimization_report.md` | Retrieval and answer metrics are separated; current manual review covers all 20 evaluation questions. |
| Open WebUI deployment | Complete | `evaluation/optimizations/create_ollama_model.py`, `evaluation/results/openwebui_final_model_smoke.json` | Final picker option is `ul-fri-slovenian-employment-law-rag-openwebui`, with `strict_legal_rag_sl_v3` and deterministic settings. |
| Standalone app | Planned, not implemented | `app_plan.md` | Intentionally not implemented for this submission; user requested plan only. |
| Fine-tuning | Exploratory only | `evaluation/fine_tuning/data/README.md`, `evaluation/optimizations/requirements-peft.txt` | Deviation: no fine-tuning because of CPU limits and lab recommendation to choose one approach. |

## Submission Requirements

| Instruction / grading point | Status | Repository evidence | Completion notes |
| --- | --- | --- | --- |
| Submission 1: select project and prepare corpus analysis | Complete | `report/report.tex`, `evaluation/optimizations/data/coleslaw_employment_summary.json`, `evaluation/optimizations/rag_optimization_report.md` | COLESLAW was analyzed as the broad corpus; final scope narrowed to Slovenian employment law. |
| Submission 1: report includes introduction, related work, initial ideas | Complete | `report/report.tex` | Final report keeps these elements but updates them for final delivery. |
| Submission 1: proposed dataset/corpus | Complete | `report/report.tex`, `evaluation/optimizations/official_sources.json` | Final corpus policy prioritizes official law over raw size. |
| Submission 1: well-organized repository | Complete | `README.md` | README now reflects actual layout instead of outdated `src/` paths. |
| Submission 2: update previous sections | Complete | `report/report.tex` | Final report supersedes the interim text. |
| Submission 2: implement at least one solution | Complete | `report/code/rag.py`, `evaluation/run_eval.py`, `evaluation/retrieval_eval.py` | Implemented lexical RAG with baseline/RAG evaluation. |
| Submission 2: include analysis and future directions | Complete | `report/report.tex`, `evaluation/optimizations/rag_optimization_report.md`, `app_plan.md` | Includes limitations, source-priority findings, and app roadmap. |
| Submission 3: final report and final solution | Complete | `report/report.tex`, `README.md`, `evaluation/` | Final report is concise and evidence-driven. |
| Submission 3: fully reproducible repository | Complete with model-availability caveat | `README.md`, `requirements.txt`, `evaluation/config.example.env` | Remote Ollama/Open WebUI was verified; GaMS still depends on being served locally. |
| Pass condition: final solution/report worth 80% | Complete | `report/report.tex`, `compliance.md` | This file documents evidence for each required item. |
| Peer review worth 20% | External | N/A | Peer review is outside repository implementation. |

## Domain-Specific Assistant Requirements

| Methodology requirement | Status | Evidence | Notes / deviation |
| --- | --- | --- | --- |
| Literature review of approaches for domain knowledge injection | Complete | `report/report.tex`, `report/report.bib` | Compares prompt engineering, RAG, fine-tuning/LoRA, and tool use. |
| Compare prompt engineering, RAG, fine-tuning | Complete | `report/report.tex`, `evaluation/optimizations/rag_optimization_report.md` | Decision: RAG-only for final work; fine-tuning deferred. |
| Data curation and domain definition | Complete | `evaluation/optimizations/official_sources.json`, `evaluation/questions.jsonl` | Domain limited to Slovenian employment law. |
| If RAG: document chunking | Complete | `report/report.tex`, `README.md`, `report/code/rag.py` | Current curated chunks are compact legal passages; future app plan calls for article-level chunks. |
| If RAG: document retrieval mechanism | Complete | `report/report.tex`, `evaluation/retrieval_eval.py`, `evaluation/retrieval_shared.py`, `report/code/rag.py` | Normalized BM25 with a simple lexical fallback for CPU reproducibility. |
| If RAG: document prompt guardrails | Complete | `evaluation/optimizations/config.json`, `evaluation/optimizations/rag_optimization_report.md` | Selected prompt is `strict_legal_rag_sl_v3`. |
| Evaluation: retrieval accuracy / relevance | Complete | `evaluation/retrieval_eval.py`, `evaluation/results/retrieval_summary.csv`, `evaluation/manual_eval_appendix.md` | Main metric is answerable Hit@3 plus false evidence and context length; Hit@1 is documented as a stricter diagnostic. |
| Evaluation: factual consistency | Complete | `evaluation/judge_eval.py`, `evaluation/results/summary_scores.csv`, `evaluation/manual_eval_appendix.md` | Current reproducible pass uses offline judge plus manual review; earlier live LLM-as-judge artifacts remain historical context. |
| Evaluation: tone and safe handling | Complete | `evaluation/questions.jsonl`, `evaluation/judge_eval.py` | Includes ambiguous and unanswerable questions; refusal accuracy is reported. |
| Human-centric metrics | Partial, improved | `evaluation/manual_eval_appendix.md`, `evaluation/results/manual_openwebui_eval_answers.jsonl`, `evaluation/results/manual_openwebui_eval_judgements.jsonl` | Added manual spot-check of all 20 final Open WebUI answers; still not a qualified legal-expert review. |
| Architecture, challenges, workflow insights | Complete | `report/report.tex`, `app_plan.md` | Report explains corpus-size vs corpus-quality tradeoff and CPU constraints. |

## High-Score Criteria

| Criterion for high marks | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Clear and runnable repository | Complete | `README.md`, `requirements.txt` | Commands are aligned with current files. |
| Well-organized report | Complete | `report/report.tex` | Report focuses on final RAG solution, results, limitations, and future work. |
| Results discussed, not only shown | Complete | `report/report.tex`, `evaluation/optimizations/rag_optimization_report.md` | Discusses why curated corpus beats larger COLESLAW sample. |
| Readable tables/figures that add value | Complete | `report/report.tex`, `evaluation/results/report.md`, `evaluation/results/*.png`, `evaluation/results/optimization/*.png`, `evaluation/results/arena_live_smoke_charts/*.png` | `matplotlib` is installed in `.venv`; charts, CSVs, and Markdown reports regenerate. |
| Sensible measures | Complete | `evaluation/retrieval_eval.py`, `evaluation/judge_eval.py` | Separates retrieval failures from generation failures. |
| Show where algorithm works and fails | Complete | `report/report.tex`, `evaluation/optimizations/rag_optimization_report.md`, `evaluation/manual_eval_appendix.md` | Works on curated statutory chunks and refusals; remaining deployed-model failures are `q009`, `q012`, and `q014`. |
| Justify differences in approaches | Complete | `report/report.tex`, `evaluation/optimizations/rag_optimization_report.md` | RAG vs fine-tuning vs prompt-only documented. |
| Beyond minimum criteria | Complete | `evaluation/optimizations/`, `app_plan.md`, `compliance.md` | Includes prompt sweep, source monitor, official-source manifest, Open WebUI export, app plan, and compliance audit. |

## Data and Source Requirements

| Requirement | Status | Evidence | Notes / deviation |
| --- | --- | --- | --- |
| Datasets available elsewhere should be linked | Complete | `report/report.bib`, `README.md` | COLESLAW linked through CLARIN.SI handle; official sources linked in manifest. |
| Transformation scripts should be included | Complete | `evaluation/optimizations/prepare_corpus.py`, `evaluation/fine_tuning/prepare_dataset.py`, `evaluation/optimizations/prepare_peft_dataset.py` | COLESLAW archive itself is not committed. |
| Include dependencies | Complete | `requirements.txt`, `evaluation/optimizations/requirements-peft.txt` | Runtime and optional PEFT dependencies are separated. |
| Include manually prepared data if needed | Complete | `report/code/data/chunk.jsonl`, `evaluation/questions.jsonl` | Small curated corpus and evaluation questions are committed. |
| Public/current source validation | Complete | `evaluation/results/optimization/official_source_monitor.json` | Latest run: 12/12 PISRS, 17/17 government/official interpretation, 1/1 case-law sources reachable. |

## Latest Compliance Check

Run date: 2026-05-21.

| Check | Status | Result |
| --- | --- | --- |
| `python -m json.tool evaluation/optimizations/config.json` | Pass | Optimization config is valid JSON and selects `strict_legal_rag_sl_v3`. |
| `python -m json.tool evaluation/optimizations/official_sources.json` | Pass | Official source manifest is valid JSON. |
| `python -m py_compile report/code/rag.py evaluation/manual_openwebui_eval.py evaluation/retrieval_eval.py evaluation/run_eval.py evaluation/judge_eval.py evaluation/optimizations/create_ollama_model.py` | Pass | Evaluation, retrieval, deployment, and manual-eval scripts compile. |
| `python evaluation/optimizations/monitor_official_sources.py` | Pass | PISRS `12/12`, government/official interpretation `17/17`, case law `1/1`. |
| `python evaluation/retrieval_eval.py --quiet` | Pass | Hit@3 `1.000`, false evidence `0.000`, average context `200.4` words. |
| `python evaluation/retrieval_eval.py --quiet --top-k 1 --output /tmp/retrieval_top1.jsonl` | Pass with known weakness | Hit@1 `0.938`; only answerable failure is `q015`, an underspecified dismissal question. |
| `python evaluation/optimizations/run_prompt_sweep.py --provider offline --model-id webui-mistral-7b --prompt-id strict_legal_rag_sl_v3 --settings-id deterministic --corpus-chunks report/code/data/chunk.jsonl --quiet` | Pass | Regenerated curated-corpus optimization answers. |
| `python evaluation/judge_eval.py --provider offline --answers evaluation/results/optimization/prompt_sweep_answers.jsonl --output evaluation/results/optimization/judgements.jsonl --quiet` | Pass | Offline RAG correctness `3.15`, grounding `3.75`, hallucination `0.85`, refusal `1.00`. |
| `python evaluation/optimizations/summarize_optimization.py` | Pass | Regenerated optimization CSV, Markdown, and charts. |
| `python evaluation/manual_openwebui_eval.py` | Pass | Collected 20 deployed Open WebUI answers with no API errors. |
| Manual review of deployed Open WebUI answers | Pass with residual risk | `17/20` correct or appropriately refused; failures documented for `q009`, `q012`, `q014`. |
| `python evaluation/run_eval.py --provider openwebui --model ul-fri-slovenian-employment-law-rag-openwebui --quiet` | Pass | Regenerated 60 main answer rows for raw prompt, baseline, and RAG variants. |
| `python evaluation/judge_eval.py --provider offline --quiet` and `python evaluation/visualize_results.py` | Pass | Regenerated main judgements, summaries, and charts. |
| `latexmk -pdf -outdir=.out report.tex` from `report/` | Pass | Rebuilt final PDF; tracked `report/report.pdf` was refreshed from `.out/report.pdf`. |

## Explicit Deviations

| Deviation | Reason | Risk mitigation |
| --- | --- | --- |
| No fine-tuning in final approach | CPU-limited machine; lab recommendation to choose one main approach; legal truth depends on current sources. | Keep PEFT scripts/data as future-only; optimize retrieval, prompt, and source freshness first. |
| No standalone app implementation | Requested scope was to plan the app, not implement it yet; course priority is NLP pipeline and evaluation. | `app_plan.md` gives PWA/Tauri/Flutter comparison and implementation phases. |
| COLESLAW extraction is not primary final corpus | The sampled extraction over-retrieves case law and old collective-agreement material. | Use curated primary-law chunks now; keep COLESLAW for case-law demo and future tertiary index. |
| No qualified human legal review included | Repository cannot substitute for legal expert validation. | Added non-expert manual spot-check appendix; final assistant remains informational and source-grounded only. |
| Live GaMS run not performed | `cjvt/GaMS-1B-Chat` was not present in the discovered Ollama/Open WebUI model list on 2026-05-21. | Keep GaMS as preferred Slovenian candidate; use `ul-fri-nlp-course-project-optimized:latest` as the best currently runnable model. |
| Some discovered models disabled in default arena | `qwen2.5-coder:7b` was available but too slow for routine smoke evaluation. | Disabled it by default and documented the reason; direct Ollama arena still covers optimized, Mistral, Llama 3, and Gemma 3 4B. |

## Final Acceptance Checklist

- [x] `report/report.tex` is a final report, not an initial project report.
- [x] No placeholder abstract remains.
- [x] README commands match the actual repository.
- [x] `requirements.txt` exists.
- [x] Official source manifest is JSON-valid.
- [x] Official source monitor was regenerated.
- [x] Live optimized-model evaluation was regenerated through remote Ollama.
- [x] Final optimized chatbot was registered and smoke-tested in Open WebUI.
- [x] Evaluation charts were regenerated from `.venv`.
- [x] Manual Open WebUI spot-check appendix added.
- [x] Fine-tuning artifacts are marked exploratory/stale for final claims.
- [x] Standalone app is planned, not implemented.
- [x] Deviations are documented and justified.

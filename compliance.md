# Compliance With NLP 2026 Project Instructions

Date: 2026-05-22

This file maps the course instructions in `instructions/Natural language processing 2026.pdf` to repository evidence for the final Slovenian employment-law RAG assistant.

## Final Status Summary

| Area | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Final solution | Complete | `report/code/rag.py`, `evaluation/`, `evaluation/optimizations/config.json` | RAG-only solution with strict v3 prompt, source-priority reranking, citation validation, and official-source monitoring. |
| Final report | Complete | `report/report.tex` | Final report focuses on the official corpus, evaluation, limitations, and reproducibility. |
| Reproducible repository | Complete | `README.md`, `requirements.txt`, `evaluation/README.md` | Offline path does not require live model endpoints. |
| Corpus and source curation | Complete | `report/code/data/chunk.jsonl`, `evaluation/optimizations/build_official_corpus.py`, `evaluation/optimizations/official_sources.json`, `evaluation/optimizations/data/official_employment_summary.json` | Committed corpus has 1,371 chunks from PISRS, official guidance, and tertiary case law. |
| Evaluation | Complete | `evaluation/questions.jsonl`, `evaluation/results/`, `evaluation/optimizations/rag_optimization_report.md` | 40-question set covers the requested employment-law topics plus ambiguity and out-of-scope refusals. |
| Open WebUI/Ollama deployment artifacts | Complete | `evaluation/optimizations/create_ollama_model.py`, `evaluation/results/openwebui_final_model_smoke.json` | Live artifacts are retained, while offline reproduction is the authoritative local path. |
| Fine-tuning | Exploratory only | `evaluation/fine_tuning/data/README.md`, `evaluation/optimizations/requirements-peft.txt` | RAG is the selected final approach because current legal sources matter more than memorized parameters. |
| Independent grading estimate | Updated | `grade.md` | Expected target is now a 9-10 candidate, with legal-expert validation as the remaining ceiling. |

## Grading Criteria Interpretation

| Rubric level | Fit to current project | Evidence |
| --- | --- | --- |
| 10 exceptional | Possible but not claimed | Strong corpus expansion and citation discipline, but no qualified legal-expert audit or user study. |
| 9 very good | Supported | Official corpus builder, 1,371 committed chunks, source-tier reranking, citation validation, larger evaluation, visualizations, and documented fixes exceed the minimum. |
| 8 good | Exceeded | Final report, implemented RAG, reproducible scripts, evaluation, limitations, and discussion satisfy the stated baseline. |
| 7 superficial | Exceeded | Repository has repeatable commands, generated artifacts, monitoring, and failure analysis. |
| 6 or lower | Not applicable | There is a working implementation and evidence for every core Domain-Specific AI Assistant requirement. |

Conservative expected cluster: **9/10**, with upside toward 10 if graders value the official corpus builder and engineering artifacts, and with downside if they require qualified legal review.

## Submission Requirements

| Instruction / grading point | Status | Repository evidence | Completion notes |
| --- | --- | --- | --- |
| Submission 1: select project and prepare corpus analysis | Complete | `report/report.tex`, `evaluation/optimizations/data/coleslaw_employment_summary.json`, `evaluation/optimizations/data/official_employment_summary.json` | COLESLAW was analyzed; final scope narrowed to official Slovenian employment-law sources. |
| Submission 1: report includes introduction, related work, initial ideas | Complete | `report/report.tex`, `report/report.bib` | Final report keeps these elements and updates them for final delivery. |
| Submission 1: proposed dataset/corpus | Complete | `evaluation/optimizations/official_sources.json`, `report/code/data/chunk.jsonl` | Source policy prioritizes PISRS, official guidance, and only then case law. |
| Submission 1: well-organized repository | Complete | `README.md` | README reflects the actual layout and reproduction commands. |
| Submission 2: update previous sections | Complete | `report/report.tex` | Final report supersedes interim text. |
| Submission 2: implement at least one solution | Complete | `report/code/rag.py`, `evaluation/run_eval.py`, `evaluation/retrieval_eval.py` | Implemented lexical RAG with baseline/RAG evaluation. |
| Submission 2: include analysis and future directions | Complete | `report/report.tex`, `evaluation/optimizations/rag_optimization_report.md` | Includes limitations, source-priority findings, and future RAG work. |
| Submission 3: final report and final solution | Complete | `report/report.tex`, `README.md`, `evaluation/` | Final report is concise and evidence-driven. |
| Submission 3: fully reproducible repository | Complete with live-model caveat | `README.md`, `requirements.txt`, `evaluation/config.example.env` | Live Ollama/Open WebUI remains optional; offline smoke mode is reproducible. |
| Peer review worth 20% | External | N/A | Peer review is outside repository implementation. |

## Domain-Specific Assistant Requirements

| Requirement | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Literature review of domain-knowledge injection | Complete | `report/report.tex`, `report/report.bib` | Compares prompting, RAG, fine-tuning/LoRA, and tool use. |
| Compare prompt engineering, RAG, fine-tuning | Complete | `report/report.tex`, `evaluation/optimizations/rag_optimization_report.md` | Final decision is RAG-only; fine-tuning remains exploratory. |
| Data curation and domain definition | Complete | `evaluation/optimizations/official_sources.json`, `evaluation/questions.jsonl` | Domain is Slovenian employment law. |
| If RAG: document chunking | Complete | `report/report.tex`, `README.md`, `evaluation/optimizations/build_official_corpus.py` | PISRS is article-level; official pages/PDF/DOCX are section-level. |
| If RAG: document retrieval mechanism | Complete | `report/report.tex`, `evaluation/retrieval_eval.py`, `evaluation/retrieval_shared.py`, `report/code/rag.py` | BM25 with lexical fallback and source-priority reranking. |
| If RAG: document prompt guardrails | Complete | `evaluation/optimizations/config.json`, `evaluation/optimizations/rag_optimization_report.md` | Selected prompt is `strict_legal_rag_sl_v3`. |
| Evaluation: retrieval accuracy / relevance | Complete | `evaluation/retrieval_eval.py`, `evaluation/results/retrieval_summary.csv` | Latest Hit@3 `1.000`, false evidence `0.000`, average context `448.6` words. |
| Evaluation: factual consistency | Complete | `evaluation/judge_eval.py`, `evaluation/results/summary_scores.csv` | Offline RAG correctness `2.95`, hallucination `1.68`, supported citations `1.00`, refusal accuracy `1.00`. |
| Evaluation: tone and safe handling | Complete | `evaluation/questions.jsonl`, `evaluation/judge_eval.py` | Includes ambiguous and unanswerable questions. |
| Human-centric metrics | Partial | `evaluation/manual_eval_appendix.md` | Non-expert manual/offline review only; no legal-expert validation. |
| Architecture, challenges, workflow insights | Complete | `report/report.tex` | Report explains source authority, corpus coverage, CPU constraints, and remaining limits. |

## Latest Compliance Check

Run date: 2026-05-22, in `.venv`.

| Check | Status | Result |
| --- | --- | --- |
| JSON validation | Pass | `evaluation/optimizations/config.json`, `official_sources.json`, summary JSON, and generated JSONL validate. |
| Python compilation | Pass | Changed evaluation, retrieval, and corpus-builder scripts compile. |
| Corpus checks | Pass | `1,371` chunks; required metadata present; PISRS article metadata present; no private grounding sources. |
| Source monitor | Pass | PISRS `12/12`, official guidance `24/24`, case law `1/1`. |
| Retrieval evaluation | Pass | Hit@3 `1.000`, false evidence `0.000`, average context `448.6` words. |
| Offline answer evaluation | Pass | RAG correctness `2.95`, grounding `4.83`, hallucination `1.68`, supported citations `1.00`, refusal accuracy `1.00`. |
| Known failure regression | Pass | `q009`, `q012`, and `q014` retrieve/cite relevant sources; `q012` uses current 30-working-day rule. |
| Optimization sweep | Pass | Offline prompt sweep regenerated over 40 questions and the expanded official corpus. |

## Explicit Limitations

| Limitation | Reason | Risk mitigation |
| --- | --- | --- |
| No qualified legal-expert review | Course repository cannot substitute for professional legal validation. | Keep assistant informational, source-grounded, and refusal-heavy. |
| No fine-tuning in final approach | CPU-limited machine and legal freshness needs. | Keep PEFT scripts/data exploratory; prioritize retrieval and source monitoring. |
| Direct sodnapraksa API not integrated | `https://sodnapraksa.si/api2/` requires permission. | Use only a bounded COLESLAW/sodnapraksa tertiary tier, suppressed for statutory questions. |
| Live GaMS run not performed | `cjvt/GaMS-1B-Chat` was not available through the discovered endpoint. | Keep GaMS as preferred Slovenian candidate; retain current runnable Open WebUI/Ollama artifacts. |

## Final Acceptance Checklist

- [x] `report/report.tex` is a final report.
- [x] README commands match the actual repository.
- [x] `requirements.txt` includes runtime and parsing dependencies.
- [x] Obsolete planning-only material was removed.
- [x] Official source manifest is JSON-valid.
- [x] Official corpus builder writes the committed RAG corpus.
- [x] Expanded corpus has more than 150 chunks.
- [x] PISRS chunks include article metadata.
- [x] Private legal portals are excluded from grounding sources.
- [x] Source monitor was regenerated on 2026-05-22.
- [x] Evaluation set has 40 questions.
- [x] Evaluation charts and CSV summaries were regenerated.
- [x] Known failures `q009`, `q012`, and `q014` are documented as fixed in the offline regression path.
- [x] Fine-tuning artifacts are marked exploratory.
- [x] Legal-review limitation remains honest.

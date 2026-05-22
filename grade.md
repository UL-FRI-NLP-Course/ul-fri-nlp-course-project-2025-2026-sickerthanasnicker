# Submission 3 Grade Estimate

Independent reviewer: spawned sub-agent `Darwin` (`019e4f26-f2b1-7580-9e16-31177f587513`)

Prompted task: inspect `instructions/Natural language processing 2026.pdf` and the repository evidence, interpret the grading criteria from the ground up, and estimate the likely Submission 3 grade for the Domain-Specific AI Assistant project. The sub-agent was instructed not to edit files.

## Estimated Grade

Estimated project grade: **8/10**

Uncertainty: likely **7.5-8.5**, rounded to the course scoring cluster **8**.

Rationale: the repository meets the main minimum criteria for a solid final project: final report, implemented RAG pipeline, curated data, reproducible scripts, evaluation artifacts, related work, discussion of RAG vs prompting vs fine-tuning, and documented limitations. It is not a confident 9 because the deployed knowledge base is small, manual review still finds factual/citation failures, and live model reproducibility depends on external Open WebUI/Ollama availability.

## Strengths

| Area | Evidence |
| --- | --- |
| Final report | `report/report.tex`, `report/report.pdf` |
| Implemented RAG pipeline | `report/code/rag.py`, `evaluation/retrieval_shared.py` |
| Curated source-of-truth corpus | `report/code/data/chunk.jsonl` |
| Evaluation set | `evaluation/questions.jsonl` with 20 factual, ambiguous, and unanswerable questions |
| Retrieval evaluation | `evaluation/retrieval_eval.py`, `evaluation/results/retrieval_summary.csv` |
| Answer evaluation | `evaluation/run_eval.py`, `evaluation/judge_eval.py`, `evaluation/results/summary_scores.csv` |
| Human-centric/manual review | `evaluation/manual_eval_appendix.md` |
| Optimization work | `evaluation/optimizations/`, `evaluation/results/optimization/` |
| Official-source monitoring | `evaluation/optimizations/official_sources.json`, `evaluation/results/optimization/official_source_monitor.json` |
| Compliance audit | `compliance.md` |

Latest local verification reports Hit@3 `1.000`, false evidence `0.000`, and average context length `199.2` words. The stricter Hit@1 diagnostic is `0.938`.

## Main Risks

- Final corpus is only 14 curated chunks, so coverage is narrow even inside Slovenian employment law.
- Manual review still reports three substantive deployed-answer failures: `q009`, `q012`, and `q014`.
- Citation discipline is incomplete: `7/11` supported citations among non-refusal factual answers in the manual review.
- Human evaluation is a non-expert spot-check, not a legal expert review or user study.
- Live Open WebUI/Ollama results are useful evidence but not fully self-contained without endpoint access.
- `report/report-new.tex` and `report/report-new.pdf` are stale interim artifacts and should not be used for final claims.

## Integration Notes

After the sub-agent returned its estimate, the following issues it identified were addressed:

- Added the missing `app_plan.md` referenced by README/compliance.
- Fixed a retrieval reproducibility bug where the evaluation index and project search could use inconsistent tokenizer/import paths when `rank-bm25` was unavailable.
- Regenerated retrieval summaries, offline optimization summaries, source monitoring, and charts from `.venv`.
- Updated report and compliance numbers to the verified `199.2` average context length.

## Bottom Line

The most defensible expected grade is **8/10**. The project is stronger than a bare minimum RAG baseline because it includes source monitoring, prompt optimization, deployment artifacts, manual review, and a detailed compliance audit. The main ceiling is the small corpus and unresolved generation/citation failures.

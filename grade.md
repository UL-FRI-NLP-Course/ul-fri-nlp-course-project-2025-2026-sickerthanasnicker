# Submission 3 Grade Estimate

Updated date: 2026-05-22

## Estimated Grade

Estimated project grade after cleanup and corpus expansion: **9/10 candidate**.

Likely range: **8.5-9.5**. A 10 remains possible only if graders do not expect qualified legal-expert validation or a user study.

## Why The Estimate Improved

| Previous risk | Current status |
| --- | --- |
| Corpus was only 14 curated chunks | Expanded to 1,371 committed chunks from official sources plus bounded tertiary case law. |
| Case law could dominate statutory retrieval | Added source-priority reranking: primary law, official interpretation, operational guidance, then case law. |
| Evaluation set was 20 questions | Expanded to 40 questions across leave/regres, fixed-term contracts, termination, severance, sick leave/ZZZS, minimum wage 2026, working-time evidence, safety, wage non-payment, collective agreements, case-law interpretation, ambiguity, and out-of-scope refusals. |
| Citation discipline was incomplete | Added citation validation; offline RAG supported-citation rate is `1.00`. |
| Known failures `q009`, `q012`, `q014` | Offline regression now retrieves/cites the relevant sources; `q012` was corrected to the current official 30-working-day rule. |
| App-plan material diluted the final evidence | Removed that material and replaced the claims with corpus, retrieval, citation, and evaluation evidence. |

## Current Evidence

| Area | Evidence |
| --- | --- |
| Final report | `report/report.tex`, `report/report.pdf` |
| RAG pipeline | `report/code/rag.py`, `evaluation/retrieval_shared.py` |
| Official corpus builder | `evaluation/optimizations/build_official_corpus.py` |
| Main RAG corpus | `report/code/data/chunk.jsonl` |
| Corpus summary | `evaluation/optimizations/data/official_employment_summary.json` |
| Source manifest and monitor | `evaluation/optimizations/official_sources.json`, `evaluation/results/optimization/official_source_monitor.json` |
| Evaluation set | `evaluation/questions.jsonl` with 40 questions |
| Retrieval evaluation | `evaluation/retrieval_eval.py`, `evaluation/results/retrieval_summary.csv` |
| Answer evaluation | `evaluation/run_eval.py`, `evaluation/judge_eval.py`, `evaluation/results/summary_scores.csv` |
| Optimization work | `evaluation/optimizations/`, `evaluation/results/optimization/` |
| Compliance audit | `compliance.md` |

Latest local verification reports:

- Corpus: `1,371` chunks.
- Source monitor: PISRS `12/12`, official guidance `24/24`, case law `1/1`.
- Retrieval: Hit@3 `1.000`, false evidence `0.000`, average context `448.6` words.
- Offline RAG answer metrics: correctness `2.95`, grounding `4.83`, hallucination `1.68`, supported citations `1.00`, refusal accuracy `1.00`.

## Remaining Risks

- No qualified legal-expert review is included.
- Offline answer quality is still limited by extractive sentence selection and a simple deterministic judge.
- Live Open WebUI/Ollama results remain endpoint-dependent, although the offline reproduction path is self-contained.
- Dense retrieval or semantic reranking could still improve answer synthesis over multi-article questions.

## Bottom Line

The repository is now stronger than a minimum final RAG project: it has a committed official corpus builder, broad official coverage, explicit source authority, citation checks, larger evaluation, and documented failure fixes. The most defensible expected grade is **9/10**.

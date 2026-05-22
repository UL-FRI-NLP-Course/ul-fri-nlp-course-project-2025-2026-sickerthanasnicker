# Grade Estimate

Updated: 2026-05-22

## Summary

Estimated Submission 3 score: **9/10**.

Defensible range: **8.5 – 9.5 / 10**.

The project addresses all minimum criteria (literature survey, data curation, implemented RAG pipeline, automated evaluation, final report, reproducible repository) and goes beyond them in several ways: source authority ordering, actor-sensitive retrieval reranking, case-law suppression for statutory questions, systematic prompt iteration across five documented versions, multi-model arena comparison, and a source freshness monitor. What prevents a clear 10 is the absence of a qualified legal-expert audit and the fact that the generated-answer correctness score, while meaningfully improved over baseline, stays in the moderate range even with the best local model.

---

## PDF Rubric Mapping

The course instructions (`instructions/Natural language processing 2026.pdf`) define six score levels.

| Level | Description |
| ---: | --- |
| 10 | Extraordinary results or quality; multiple novel ideas executed well; only very minor room for improvement |
| 9 | Above average; novel ideas visible but some flaws or polish missing |
| 8 | Solid, addresses the given instructions only; not investigated further |
| 7 | Below average; partial understanding; errors |
| 6 | Minimum criteria addressed with major errors or drawbacks |
| 5 | Minimum criteria not fully addressed; major flaws; insufficient effort |

Submission 3 counts for **80 %** of the lab grade; peer review counts for the remaining **20 %** and is outside this repository.

---

## Criterion Breakdown

### Domain definition and data curation

Estimate: 9. The domain is narrow and explicit: Slovenian employment-law question answering, covering contracts, termination, leave, wages, working time, sick leave, collective employment issues, and closely related statutory guidance.

Evidence:

- Source manifest: `evaluation/optimizations/official_sources.json` — 12 PISRS sources, 24 government or official interpretation/operational sources, 1 case-law index.
- Corpus builder: `src/ul_fri_nlp/optimizations/build_official_corpus.py` — downloads current official sources, applies source-type tagging, and writes reproducible chunks.
- Committed corpus: `report/code/data/chunk.jsonl` — 1,371 chunks (1,059 primary-law, 189 official interpretation, 93 operational guidance, 30 tertiary case law).
- Corpus summary: `evaluation/optimizations/data/official_employment_summary.json`.
- Source monitor: `evaluation/results/optimization/official_source_monitor.json` — 12/12 PISRS, 24/24 government, 1/1 case-law reachable.

The project started with the broad COLESLAW 1.0 corpus and identified that a corpus dominated by court records and non-employment documents gave short contexts and missed key retrieval targets. Moving to a curated official corpus fixed every tracked regression and tripled average context length (199 → 1,430 words).

Strength: source priority ordering (primary law > official interpretation > operational guidance > case law) is enforced both in retrieval scoring and in the system prompt.

### Literature review and related work

Estimate: 8.5.

Evidence:

- `report/report.tex`, sections Related Work and System.
- `report/report.bib` — Lewis 2020 (RAG), Hu 2021 (LoRA), Schick 2023 (Toolformer), Song 2025 (injection survey), COLESLAW 2024, PISRS ZDR-1, GOV.SI, ZZZS, OPSI, Pravko.si, MojMaliPravnik.net, GaMS-1B-Chat.
- Explicit comparison of prompting, RAG, fine-tuning, and tool use with justification for the chosen RAG-first path.

Existing Slovenian legal tools (Pravko, MojMaliPravnik) are acknowledged as demand evidence but correctly noted as lacking reproducible pipelines or controlled source policies.

### Implementation

Estimate: 9.

Evidence:

- Runtime retriever: `src/ul_fri_nlp/app/rag.py` — BM25 (with `SimpleLexicalIndex` fallback), Slovenian stopword removal, light stemming, out-of-scope token filter, `actor_adjustment` for employer/employee questions, `source_priority_adjustment` for source authority and case-law suppression.
- Shared evaluation retriever: `src/ul_fri_nlp/evaluation/retrieval_shared.py` — same logic as runtime so retrieval scores correspond to actual answer-time behaviour.
- Five documented system prompt iterations (`strict_grounded_v1` → `citation_first_v1` → `ambiguity_aware_v1` → `strict_legal_rag_sl_v2` → `strict_legal_rag_sl_v3`) with explicit rationale for each change, stored in `evaluation/optimizations/config.json`.
- Multi-model arena comparison: llama3, mistral:7b, gemma3:4b, qwen2.5-coder:7b, qwen3-coder-30b-a3b.
- Fine-tuning data prepared (`evaluation/optimizations/data/peft_train.jsonl` 176 rows, `peft_dev.jsonl` 44 rows) and consciously not used for the final system, with documented rationale (CPU-limited hardware; legal freshness requires retrieved current sources, not memorised parameters).
- Deployment through Ollama (`ul-fri-slovenian-employment-law-rag:latest`) and Open WebUI (`ul-fri-slovenian-employment-law-rag-openwebui` at `https://ai.koderverse.com/`).

Novel implementation choices above the minimum criteria:

- Source-type score bonus (`primary_law` +7.0, `official_interpretation` +2.5, `official_operational_guidance` +2.0) applied at retrieval time.
- `actor_adjustment` reranker for employer/employee actor disambiguation.
- Hard case-law suppression (`−100` score penalty) for statutory questions unless the query explicitly asks about court practice.
- Out-of-scope token set that filters queries mentioning DDV, inheritance, property, Austrian law, etc. before retrieval even runs.
- Ambiguity guardrail in v3 prompt: short or underspecified questions get an explicit missing-context warning before any substantive answer.

### Evaluation

Estimate: 9.

Evidence:

- Evaluation set: `evaluation/questions.jsonl` — 40 questions across 12 topic areas (annual leave/regres, fixed-term contracts, termination, severance, sick leave/ZZZS, minimum wage 2026, working-time evidence, occupational safety, wage non-payment, collective agreements, case-law interpretation, ambiguous and unanswerable).
- Retrieval and generation evaluated separately, which makes failures diagnosable.
- Unanswerable and out-of-scope questions tested explicitly; refusal accuracy tracked.
- Multiple evaluation tracks: offline deterministic (reproducibility), optimization sweep (real model quality), live arena (multi-model comparison), manual appendix.

Final metrics from committed result files:

| File | Metric | Value |
| --- | --- | --- |
| `evaluation/results/retrieval_summary.csv` | Answerable Hit@3 | **1.000** |
| `evaluation/results/retrieval_summary.csv` | Unanswerable false-evidence rate | **0.000** |
| `evaluation/results/retrieval_summary.csv` | Average context length (words) | **1430.8** |
| `evaluation/results/optimization/optimization_summary.csv` | RAG correctness (mistral+v3) | **2.95 / 5** |
| `evaluation/results/optimization/optimization_summary.csv` | RAG hallucination (mistral+v3) | **1.68 / 5** |
| `evaluation/results/optimization/optimization_summary.csv` | Supported citation rate | **1.00** |
| `evaluation/results/optimization/optimization_summary.csv` | Refusal accuracy | **1.00** |
| `evaluation/results/summary_scores.csv` | Baseline correctness | **0.50 / 5** |
| `evaluation/results/summary_scores.csv` | Baseline hallucination | **4.12 / 5** |

Three specific regression failures identified in the COLESLAW-based corpus (q009 fixed-term duration, q012 sick-pay payer, q014 ambiguous leave) are tracked and verified fixed in the official corpus.

Limitation acknowledged: the offline judge is a deterministic reproducibility proxy, not a qualified legal expert.

### Final report

Estimate: 8.5 – 9.

Evidence:

- `report/report.tex` — LaTeX source following the course template (`ds_report.cls`).
- Sections: Motivation, Related Work, Corpus and Sources, System, Evaluation, Reproducibility and Compliance, Limitations and Future Work.
- Compact results tables with comparative data.
- Limitations stated honestly.
- `report/report.bib` with 14 cited references.
- Built with `make report` into `report/.out/report.pdf`.

### Reproducibility

Estimate: 9.

Evidence:

- `Makefile` with targets: `setup`, `verify` (json-check + compile + retrieval + offline-eval + report), `corpus`, `source-monitor`, `retrieval`, `offline-eval`, `report`, `clean-report`, `clean-pyc`.
- `requirements.txt` — runtime Python dependencies.
- `evaluation/optimizations/requirements-peft.txt` — optional PEFT dependencies separated.
- `evaluation/config.example.env` — endpoint template with no committed secrets.
- `.env` ignored by git.
- Offline path runs entirely without a model server, using the deterministic stub; live Ollama/Open WebUI paths are optional.
- Open WebUI deployed at `https://ai.koderverse.com/`.

Clean-clone reproducibility command:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make verify
```

---

## Strengths

- Narrow, well-defined domain with verifiable official sources.
- Source authority ordering enforced at retrieval and prompt level (primary law first, case law suppressed).
- Actor-sensitive retrieval reranker for employer/employee question disambiguation.
- Systematic five-step prompt iteration with documented rationale.
- Multi-model arena evaluation demonstrating RAG benefit is model-independent.
- Fine-tuning consciously explored and consciously rejected with documented reasoning.
- Source freshness monitor checking 37 official sources.
- Three concrete regression fixes tracked from failure to pass.
- Deterministic offline pipeline for peer-reviewer reproducibility.
- Deployed Open WebUI instance at `https://ai.koderverse.com/`.

## Risks / Limitations

- No qualified legal-expert audit; correctness of individual answers is not certified.
- Offline judge is a reproducible regression proxy, not a human evaluation.
- RAG answer correctness/completeness at 2.95/5 with the best local model — informational assistant rather than legal advisor.
- BM25 retrieval may miss semantic paraphrases; no dense embeddings or learned reranker in the final pipeline.
- GaMS-1B-Chat (preferred Slovenian-focused model) not yet served on the local endpoint; current deployment uses mistral:7b.

## Bottom Line

Score **9/10**. The project goes meaningfully beyond minimum criteria through its source authority framework, domain-specific retrieval adjustments, and systematic prompt iteration. The gap to a 10 is the absence of expert legal validation and moderate generated-answer scores — honest limitations for a CPU-limited course prototype.

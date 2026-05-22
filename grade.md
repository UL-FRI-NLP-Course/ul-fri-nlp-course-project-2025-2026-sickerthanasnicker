# Grade Estimate For Manual Review

Updated: 2026-05-22

## Estimate

Estimated Submission 3 score: **9/10 candidate**.

Defensible range: **8.5-9.2/10**. I would not claim a clear 10 because the system has no qualified legal-expert audit or real user study, and the answer-generation score is still moderate even though retrieval and grounding are strong.

Course weighting from `instructions/Natural language processing 2026.pdf`: Submission 3 is the final solution and report worth **80%** of the lab grade; peer review is a separate obligation worth **20%**. The PDF says a score of 8 corresponds to solidly fulfilling the instructions, 9 to above-average work with some flaws, and 10 to exceptional results, quality, or structure with only very minor room for improvement.

## Current Metrics To Quote

From `evaluation/results/retrieval_summary.csv`:

| Metric | Current value |
| --- | ---: |
| `answerable_hit_rate` | `1.0` |
| `unanswerable_false_evidence_rate` | `0.0` |
| `average_context_length_words` | `1430.8` |

From `evaluation/results/summary_scores.csv`:

| model_id | variant | n | correctness | grounding | completeness | clarity | hallucination | supported_citation_rate | refusal_accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `offline-llama3:latest` | `baseline` | 40 | `0.5` | `0.125` | `0.5` | `5.0` | `4.125` | `0.0` | `0.0` |
| `offline-llama3:latest` | `rag` | 40 | `2.45` | `4.65` | `2.45` | `4.55` | `2.1` | `0.9696969696969697` | `1.0` |
| `raw-rag-prompt` | `raw_rag_prompt` | 40 | `1.5` | `5.0` | `1.5` | `3.25` | `0.0` | `0.0` | `1.0` |

Interpretation for reviewers: retrieval is excellent on the project's 40-question set, and RAG strongly improves grounding, refusal behavior, citation support, and hallucination versus the no-context baseline. The main weakness is answer completeness/correctness, which is improved but not expert-level.

## Rubric Rationale

### Final report, analysis, and discussion

Estimate: **high 8 to 9**.

Evidence:

- Final report source: `report/report.tex`.
- Generated report PDF: `report/.out/report.pdf`.
- Top-level report PDFs are intentionally removed/ignored; `.gitignore` ignores `/report/*.pdf`, and current generated report artifacts live under `report/.out/`.
- The report is concise and follows the course template style: motivation, related work, corpus/source policy, system, evaluation, reproducibility/compliance, limitations, and references.
- Results are presented in compact tables and tied to concrete claims: official corpus size, Hit@3, false-evidence rate, answer metrics, and regression fixes.

Risk: the report is strong for a course RAG project, but the evaluation discussion still relies on deterministic/offline judging rather than legal-domain expert scoring.

### Data curation and domain definition

Estimate: **9**.

Evidence:

- Domain is narrow and explicit: Slovenian employment-law question answering.
- Source manifest: `evaluation/optimizations/official_sources.json`.
- Corpus builder: `evaluation/optimizations/build_official_corpus.py`.
- Committed transformed corpus: `report/code/data/chunk.jsonl`.
- Corpus summary: `evaluation/optimizations/data/official_employment_summary.json`.
- Current corpus has 1,371 chunks: 1,059 primary-law chunks, 189 official-interpretation chunks, 93 official-operational-guidance chunks, and 30 tertiary case-law chunks.
- Source monitor snapshot: `evaluation/results/optimization/official_source_monitor.json`, reporting 12/12 PISRS sources, 24/24 government/official sources, and 1/1 case-law source reachable.

Strength: the project does not treat private legal portals as authoritative grounding sources and explicitly orders sources by authority.

### Implementation

Estimate: **8.5 to 9**.

Evidence:

- Main answer-time retriever: `report/code/rag.py`.
- Shared retrieval logic used by evaluation: `evaluation/retrieval_shared.py`.
- Evaluation scripts: `evaluation/retrieval_eval.py`, `evaluation/run_eval.py`, `evaluation/judge_eval.py`, `evaluation/visualize_results.py`.
- Final prompt/model configuration: `evaluation/optimizations/config.json`.
- Optional deployment/export artifacts: `evaluation/optimizations/webui/optimized_model_preset.json`, `evaluation/optimizations/webui/openwebui_create_model_payload.json`, `evaluation/optimizations/ollama/Modelfile`.
- Exploratory fine-tuning utilities are present but correctly scoped as non-final artifacts: `evaluation/fine_tuning/` and `evaluation/optimizations/prepare_peft_dataset.py`.

Strength: the implementation chooses a reproducible RAG path over heavier fine-tuning, which is appropriate for legal freshness and CPU-limited reproduction.

Risk: retrieval is lexical BM25 rather than dense retrieval/reranking, so semantic paraphrases and multi-hop legal questions may still be fragile.

### Evaluation

Estimate: **8.5 to 9**.

Evidence:

- Evaluation set: `evaluation/questions.jsonl` with 40 questions.
- Main generated answers: `evaluation/results/answers.jsonl`.
- Main judgements: `evaluation/results/judgements.jsonl`.
- Retrieval traces: `evaluation/results/retrieval.jsonl`.
- Generated summaries/charts: `evaluation/results/summary_scores.csv`, `evaluation/results/retrieval_summary.csv`, `evaluation/results/report.md`, plus PNG/SVG/JPG charts in `evaluation/results/`.
- Optimization evidence: `evaluation/results/optimization/optimization_report.md`, `evaluation/results/optimization/optimization_summary.csv`, and `evaluation/results/optimization/optimization_retrieval_summary.csv`.

Strength: retrieval is evaluated separately from generation, unanswerable/refusal behavior is measured, and citation support is tracked.

Risk: offline judging is reproducible but not a replacement for expert legal review. The RAG answer correctness score `2.45/5` and completeness `2.45/5` should be read honestly; the project is best defended as a strong grounded assistant prototype, not a production legal advisor.

### Reproducibility

Estimate: **9**.

Evidence:

- Setup and workflow documentation: `README.md`.
- Dependency list: `requirements.txt`.
- Reproduction targets: `Makefile`.
- Example environment variables without secrets: `evaluation/config.example.env`.
- Local generated PDF path: `report/.out/report.pdf`.
- Top-level report PDFs are removed/ignored so stale PDFs do not conflict with the reproducible build path.

Recommended reviewer commands:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make verify
```

Useful narrower commands:

```bash
make retrieval
make offline-eval
make report
make source-monitor
```

Equivalent explicit commands:

```bash
python evaluation/retrieval_eval.py --quiet
python evaluation/run_eval.py --provider offline
python evaluation/judge_eval.py --provider offline
python evaluation/visualize_results.py
mkdir -p report/.out
cd report/.out && TEXINPUTS=..: pdflatex -interaction=nonstopmode -halt-on-error ../report.tex
```

Risk: live Ollama/Open WebUI runs depend on local endpoints and model availability, so the cleanest peer-review path is the deterministic offline pipeline.

## Strengths

- Clear domain boundary and safety posture for Slovenian employment law.
- Strong official-source policy: PISRS first, official guidance second, case law only as tertiary support.
- Committed corpus and scripts for rebuilding it from official sources.
- Retrieval and generation are evaluated separately, which makes failures easier to diagnose.
- Current main retrieval metrics are excellent: Hit@3 `1.0`, false evidence `0.0`.
- RAG sharply improves over baseline on grounding, hallucination, citation support, and refusal accuracy.
- The report and README are reviewer-oriented and point to concrete reproduction commands.

## Main Risks For Graders

- No qualified legal-expert validation or user study.
- Main RAG answer correctness/completeness scores are only `2.45/5`, even though grounding is high.
- The offline judge is deterministic and useful for reproducibility, but it is still a proxy metric.
- BM25 retrieval may miss semantic paraphrases that a dense retriever or reranker could catch.
- Some live-model claims are endpoint-dependent; peer reviewers should grade the committed offline path first.

## Peer Review Expectation

The PDF says peer review is worth **20%** and asks each group to review two repositories of the same topic, follow the scoring criteria, and include feedback justifying the mark. For this repository, a fair peer review should:

- run or at least inspect `make verify`, `make retrieval`, `make offline-eval`, and `make report`;
- read `report/report.tex` or `report/.out/report.pdf`;
- verify the exact metrics in `evaluation/results/retrieval_summary.csv` and `evaluation/results/summary_scores.csv`;
- inspect the source/corpus evidence in `evaluation/optimizations/official_sources.json`, `evaluation/optimizations/data/official_employment_summary.json`, and `report/code/data/chunk.jsonl`;
- judge whether the limitations are acceptable for a course prototype rather than assuming legal correctness from fluent answers.

## Bottom Line

This is stronger than a minimum "8" submission because it includes a documented official corpus, source monitoring, reproducible evaluation, citation/refusal checks, optimization artifacts, and a concise report with limitations. The most defensible manual estimate is **9/10**, with the main downward pressure coming from the lack of expert legal validation and only moderate generated-answer correctness/completeness.

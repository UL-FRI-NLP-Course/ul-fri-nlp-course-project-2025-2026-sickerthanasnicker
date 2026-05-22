# Slovenian Employment-Law RAG Assistant

This repository is the final UL FRI Natural Language Processing 2025/2026 project for a domain-specific AI assistant. The assistant answers Slovenian employment-law questions, grounds answers in official sources, cites retrieved material, and refuses unsupported or out-of-scope questions.

The final approach is retrieval-augmented generation (RAG). Fine-tuning utilities are included as exploratory artifacts, but the submitted system relies on source curation, retrieval, prompt guardrails, and evaluation because legal correctness depends on current official sources more than on model memory.

## Reviewer Checklist

A clean clone should let a reviewer:

1. Install Python dependencies from `requirements.txt`.
2. Inspect or rebuild the official employment-law corpus.
3. Run deterministic offline retrieval and answer-evaluation checks without any model server.
4. Optionally run live Ollama/Open WebUI generation.
5. Build the report PDF into `report/.out/report.pdf`.
6. Verify which course requirements are covered in `compliance.md` and the estimated grade in `grade.md`.

The main reproducible command is:

```bash
make setup
make verify
```

`make verify` validates JSON configuration, compiles Python files, reruns retrieval metrics, reruns the deterministic offline generation/judge/charts pipeline, and builds the report into `report/.out/`.

## Requirements

Python:

- Python 3.10 or newer.
- Packages in `requirements.txt`.

System tools:

- TeX Live with `pdflatex` and `bibtex` for the report PDF.
- Optional `latexmk` for editor-driven report builds.
- Network access only when rebuilding the official corpus or checking live official-source availability.
- Optional `ollama` or Open WebUI access for live generation and deployment.

Optional PEFT/fine-tuning dependencies are intentionally separated in `evaluation/optimizations/requirements-peft.txt` because they are not required for the final RAG pipeline.

## Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create a local environment file only if you want live model calls:

```bash
cp evaluation/config.example.env .env
```

`.env` is ignored by git. The scripts accept both the project variable names and common aliases:

- `OLLAMA_HOST` or `OLLAMA_URL`
- `WEBUI_HOST`, `OPENWEBUI_HOST`, or `OPENWEBUI_URL`
- `WEBUI_API_KEY` or `OPENWEBUI_API_KEY`
- `OPENAI_API_KEY` for optional OpenAI-compatible judging/generation

## Repository Layout

```text
.
├── Makefile
├── README.md
├── compliance.md
├── grade.md
├── requirements.txt
├── pyproject.toml
├── src/
│   └── ul_fri_nlp/
│       ├── app/
│       │   └── rag.py
│       ├── evaluation/
│       │   ├── run_eval.py
│       │   ├── judge_eval.py
│       │   ├── retrieval_eval.py
│       │   ├── retrieval_shared.py
│       │   └── visualize_results.py
│       ├── fine_tuning/
│       │   └── prepare_dataset.py
│       └── optimizations/
│           ├── build_official_corpus.py
│           ├── create_ollama_model.py
│           ├── monitor_official_sources.py
│           └── run_prompt_sweep.py
├── evaluation/
│   ├── questions.jsonl
│   ├── config.json
│   ├── config.example.env
│   ├── results/
│   ├── fine_tuning/
│   └── optimizations/
│       ├── official_sources.json
│       ├── config.json
│       ├── data/
│       └── ollama/
├── report/
│   ├── report.tex
│   ├── report.bib
│   ├── .latexmkrc
│   └── code/
│       └── data/chunk.jsonl
└── instructions/
    └── Natural language processing 2026.pdf
```

## Data And Corpus

The committed RAG corpus is `report/code/data/chunk.jsonl`. It currently contains 1,371 chunks:

- 1,059 PISRS article-level primary-law chunks.
- 189 official interpretation chunks.
- 93 official operational-guidance chunks.
- 30 tertiary COLESLAW/sodnapraksa case-law chunks.

The source manifest is `evaluation/optimizations/official_sources.json`. It covers PISRS, GOV.SI, MDDSZ, ZZZS, IRSD, eUprava, SPOT, ESS, OPSI, and sodnapraksa.si sources.

Check source availability:

```bash
make source-monitor
```

Rebuild the corpus from official sources:

```bash
make corpus
```

Equivalent explicit command:

```bash
python -m ul_fri_nlp.optimizations.build_official_corpus \
  --output report/code/data/chunk.jsonl \
  --include-case-law \
  --max-case-law-chunks 30
```

COLESLAW is used only as bounded tertiary support and as an exploratory source. The original archive is not committed; the preprocessing script expects a local `corpus/COLESLAW.zip` when regenerating COLESLAW-derived chunks.

## Source Policy

The assistant follows a strict authority order:

1. PISRS statutes and consolidated law texts are canonical.
2. GOV.SI, MDDSZ, ZZZS, IRSD, eUprava, SPOT, ESS, and OPSI are official explanations or operational sources.
3. sodnapraksa.si and COLESLAW case-law chunks are tertiary support.
4. Private portals, blogs, forums, and unofficial summaries are not used as grounded answer sources.

Retrieval reranking follows `primary_law > official_interpretation > official_operational_guidance > official_case_law`. Case-law chunks are suppressed for statutory questions unless the user explicitly asks about court practice or interpretation.

## Evaluation

The evaluation set is `evaluation/questions.jsonl` and contains 40 factual, ambiguous, and unanswerable questions. Retrieval is evaluated separately from generation so failures can be traced to either missing evidence or answer synthesis.

Run retrieval metrics:

```bash
make retrieval
```

Run deterministic offline generation, judging, and charts:

```bash
make offline-eval
```

Run the same commands manually:

```bash
python -m ul_fri_nlp.evaluation.retrieval_eval
python -m ul_fri_nlp.evaluation.run_eval --provider offline
python -m ul_fri_nlp.evaluation.judge_eval --provider offline
python -m ul_fri_nlp.evaluation.visualize_results
```

The current reported retrieval result for the 40-question set is Hit@3 `1.000`, false evidence `0.000`, and average context length about `1430.8` words. Offline answer judging is a deterministic reproducibility check, not a substitute for expert legal review.

For live model comparison, configure `.env`, then run:

```bash
python -m ul_fri_nlp.evaluation.list_models --provider ollama
python -m ul_fri_nlp.evaluation.run_eval --arena
python -m ul_fri_nlp.evaluation.judge_eval
python -m ul_fri_nlp.evaluation.visualize_results
```

## Report Build

Generated report files are intentionally ignored by git. Build artifacts always go under `report/.out/`.

```bash
make report
```

Equivalent manual command:

```bash
mkdir -p report/.out
cd report/.out
TEXINPUTS=..: pdflatex -interaction=nonstopmode -halt-on-error ../report.tex
BIBINPUTS=..: bibtex report
TEXINPUTS=..: pdflatex -interaction=nonstopmode -halt-on-error ../report.tex
TEXINPUTS=..: pdflatex -interaction=nonstopmode -halt-on-error ../report.tex
```

The resulting PDF is:

```text
report/.out/report.pdf
```

Clean report artifacts:

```bash
make clean-report
```

## Deployment

### Offline Smoke Mode

Offline mode is the fully reproducible baseline. It does not call an external model and is suitable for peer reviewers:

```bash
python -m ul_fri_nlp.evaluation.run_eval --provider offline
python -m ul_fri_nlp.evaluation.judge_eval --provider offline
```

### Ollama

Set `OLLAMA_HOST` or `OLLAMA_URL` in `.env`, then verify available models:

```bash
python -m ul_fri_nlp.evaluation.list_models --provider ollama
```

Create or refresh the optimized Ollama model:

```bash
python -m ul_fri_nlp.optimizations.create_ollama_model --verify
```

Run it directly:

```bash
ollama run ul-fri-slovenian-employment-law-rag
```

Evaluate it:

```bash
python -m ul_fri_nlp.evaluation.run_eval \
  --provider ollama \
  --model ul-fri-slovenian-employment-law-rag:latest \
  --output evaluation/results/optimized_ollama_answers.jsonl
```

### Open WebUI

Set `WEBUI_HOST` and `WEBUI_API_KEY` in `.env`, then verify models:

```bash
python -m ul_fri_nlp.evaluation.list_models --provider openwebui
```

Register the final Open WebUI preset, if your API key has permission:

```bash
python -m ul_fri_nlp.optimizations.create_ollama_model \
  --skip-create \
  --register-openwebui \
  --smoke-openwebui
```

The documented final option is `ul-fri-slovenian-employment-law-rag-openwebui`, backed by the strict `strict_legal_rag_sl_v3` prompt and deterministic generation settings.

## Development Notes

- The answer-time retriever lives in `src/ul_fri_nlp/app/rag.py`.
- Shared evaluation retrieval helpers live in `src/ul_fri_nlp/evaluation/retrieval_shared.py`.
- The final prompt and model/deployment configuration live in `evaluation/optimizations/config.json`.
- Generated Python bytecode, local virtual environments, secrets, and report builds are ignored.
- Evaluation result snapshots are kept in `evaluation/results/` so reviewers can inspect the evidence behind the report tables.

## Course Compliance

The project instructions require a final report with analyses and discussion, a fully reproducible repository, linked or included dependencies/corpora, runnable code, sensible evaluation, readable results, and clear limitations. This repository addresses those requirements through:

- final report source in `report/report.tex`;
- source manifest in `evaluation/optimizations/` and corpus builder in `src/ul_fri_nlp/optimizations/`;
- committed transformed corpus and evaluation questions;
- deterministic offline evaluation path;
- optional live deployment through Ollama/Open WebUI;
- compliance and grading ledgers in `compliance.md` and `grade.md`.

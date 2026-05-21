# Slovenian Employment-Law RAG Assistant

This repository contains the UL FRI NLP 2025/2026 course project for a Slovenian employment-law question-answering assistant. The final project scope is deliberately narrow: answer questions about Slovenian employment law in Slovenian, cite official sources, and refuse questions that are outside scope or unsupported by retrieved context.

The selected approach is retrieval-augmented generation (RAG). We do not fine-tune by default because the target machine is CPU-limited and the lab guidance recommended choosing one main approach. Fine-tuning artifacts in the repository are exploratory preparation data only.

## Current Status

Implemented:

- curated BM25 RAG corpus in `report/code/data/chunk.jsonl`;
- retrieval and answer-evaluation pipeline in `evaluation/`;
- RAG optimization track with strict Slovenian legal system prompts in `evaluation/optimizations/`;
- official source manifest and monitor for PISRS, GOV.SI, MDDSZ, IRSD, eUprava, SPOT, ESS, OPSI, and sodnapraksa.si;
- Open WebUI/Ollama export files for the selected strict RAG prompt;
- standalone app design plan in `app_plan.md`;
- grading and instruction compliance ledger in `compliance.md`.

The best current result is strict RAG over the curated primary-law chunks. The COLESLAW extraction is kept as secondary/case-law support because the current 500-chunk sample is dominated by case law and old sector-specific material.

## Setup

Recommended Python setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

System tools used by the report workflow:

- `latexmk` and a TeX Live installation for the PDF report;
- optional `ollama` or Open WebUI access for live model generation;
- optional Poppler tools such as `pdftotext` for inspecting the course PDF.

The scripts load a root `.env` file if present. Start from:

```bash
cp evaluation/config.example.env .env
```

For existing setups, the scripts accept both `OLLAMA_HOST` and `OLLAMA_URL`, and both `WEBUI_HOST`/`WEBUI_API_KEY` and `OPENWEBUI_URL`/`OPENWEBUI_API_KEY`.

## Reproducible Commands

Validate official sources:

```bash
python -m json.tool evaluation/optimizations/official_sources.json >/tmp/official_sources.json
python evaluation/optimizations/monitor_official_sources.py
```

Evaluate retrieval on the curated RAG corpus:

```bash
python evaluation/retrieval_eval.py
```

Run deterministic offline generation and judging smoke tests:

```bash
python evaluation/run_eval.py --provider offline
python evaluation/judge_eval.py --provider offline
python evaluation/visualize_results.py
```

Run the optimization prompt sweep without live model calls:

```bash
python evaluation/optimizations/run_prompt_sweep.py \
  --provider offline \
  --model-id webui-mistral-7b \
  --prompt-id strict_legal_rag_sl_v2 \
  --settings-id deterministic

python evaluation/judge_eval.py \
  --provider offline \
  --answers evaluation/results/optimization/prompt_sweep_answers.jsonl \
  --output evaluation/results/optimization/judgements.jsonl

python evaluation/optimizations/summarize_optimization.py
```

Build the report:

```bash
cd report
latexmk -pdf -outdir=.out report.tex
```

If `latexmk` is unavailable, open the tracked `report/report.pdf` or compile with your local LaTeX editor.

## Repository Layout

```text
.
├── app_plan.md
├── compliance.md
├── evaluation/
│   ├── questions.jsonl
│   ├── run_eval.py
│   ├── judge_eval.py
│   ├── retrieval_eval.py
│   ├── results/
│   └── optimizations/
│       ├── config.json
│       ├── official_sources.json
│       ├── monitor_official_sources.py
│       └── rag_optimization_report.md
├── report/
│   ├── report.tex
│   ├── report.bib
│   └── code/
│       ├── rag.py
│       └── data/chunk.jsonl
└── instructions/
    └── Natural language processing 2026.pdf
```

## Source Policy

The answer corpus should use official sources only:

1. PISRS statutes and consolidated texts are canonical.
2. GOV.SI, MDDSZ, IRSD, eUprava, SPOT, ESS, and OPSI are official explanations or operational registers.
3. `sodnapraksa.si` and COLESLAW case-law chunks are secondary demo support only.
4. Private legal portals, blogs, forums, and unofficial summaries are excluded from grounded answers.

## Model Choice

The preferred Slovenian CPU-friendly candidate remains `cjvt/GaMS-1B-Chat` once it is served through Open WebUI or another compatible endpoint. It was not present in the discovered local model list during the 2026-05-21 verification run, so the current best runnable model is `ul-fri-nlp-course-project-optimized:latest` on the remote Ollama endpoint. `mistral:7b`, `llama3:latest`, and `gemma3:4b` are kept as comparison/fallback models.

The final assistant behavior is controlled mainly by `strict_legal_rag_sl_v2`: strict Slovenian answers, employment-law scope checks, source-priority rules, citation discipline, and refusal for unsupported questions.

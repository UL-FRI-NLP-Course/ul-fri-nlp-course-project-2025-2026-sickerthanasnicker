# Slovenian Employment-Law RAG Assistant

This repository contains the UL FRI NLP 2025/2026 course project for a Slovenian employment-law question-answering assistant. The final project scope is deliberately narrow: answer questions about Slovenian employment law in Slovenian, cite official sources, and refuse questions that are outside scope or unsupported by retrieved context.

The selected approach is retrieval-augmented generation (RAG). We do not fine-tune by default because the target machine is CPU-limited and the lab guidance recommended choosing one main approach. Fine-tuning artifacts in the repository are exploratory preparation data only.

## Current Status

Implemented:

- expanded official RAG corpus in `report/code/data/chunk.jsonl`;
- official corpus builder in `evaluation/optimizations/build_official_corpus.py`;
- retrieval and answer-evaluation pipeline in `evaluation/`;
- RAG optimization track with strict Slovenian legal system prompts in `evaluation/optimizations/`;
- official source manifest and monitor for PISRS, GOV.SI, MDDSZ, ZZZS, IRSD, eUprava, SPOT, ESS, OPSI, and sodnapraksa.si;
- Open WebUI/Ollama export files for the selected strict RAG prompt;
- grading and instruction compliance ledger in `compliance.md`.

The best current result is strict RAG over an official-plus-case-law corpus built from current official sources. The committed corpus contains 1,371 chunks: 1,059 PISRS article chunks, 189 official interpretation chunks, 93 official operational-guidance chunks, and 30 tertiary COLESLAW/sodnapraksa case-law chunks. Case law is suppressed for statutory questions unless the question asks for practice or interpretation.

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

Rebuild the official RAG corpus:

```bash
python evaluation/optimizations/build_official_corpus.py \
  --output report/code/data/chunk.jsonl \
  --include-case-law \
  --max-case-law-chunks 30
```

Evaluate retrieval on the committed RAG corpus:

```bash
python evaluation/retrieval_eval.py
python evaluation/retrieval_eval.py --quiet --top-k 1 --output /tmp/retrieval_top1.jsonl
```

The main reported retrieval number is Hit@3. The current 40-question set reports Hit@3 `1.000`, false evidence `0.000`, and average context length `448.6` words. The top-1 command is a stricter diagnostic.

Run deterministic offline generation and judging smoke tests:

```bash
python evaluation/run_eval.py --provider offline
python evaluation/judge_eval.py --provider offline
python evaluation/visualize_results.py
```

Manual/offline review notes are in `evaluation/manual_eval_appendix.md`. Existing Open WebUI raw outputs remain historical artifacts because live endpoint availability is external to the offline reproducibility path.

Refresh the manual answer collection from the deployed Open WebUI model:

```bash
python evaluation/manual_openwebui_eval.py
```

Run the optimization prompt sweep without live model calls:

```bash
python evaluation/optimizations/run_prompt_sweep.py \
  --provider offline \
  --model-id webui-mistral-7b \
  --prompt-id strict_legal_rag_sl_v3 \
  --settings-id deterministic \
  --corpus-chunks report/code/data/chunk.jsonl

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
├── compliance.md
├── evaluation/
│   ├── questions.jsonl
│   ├── run_eval.py
│   ├── judge_eval.py
│   ├── retrieval_eval.py
│   ├── results/
│   └── optimizations/
│       ├── build_official_corpus.py
│       ├── config.json
│       ├── data/official_employment_summary.json
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
2. GOV.SI, MDDSZ, ZZZS, IRSD, eUprava, SPOT, ESS, and OPSI are official explanations or operational registers.
3. `sodnapraksa.si` and COLESLAW case-law chunks are tertiary support only.
4. Private legal portals, blogs, forums, and unofficial summaries are excluded from grounded answers.

Retrieval reranking follows `primary_law > official_interpretation > official_operational_guidance > official_case_law`. Case-law chunks are kept out of statutory top results unless the question asks about practice, courts, or interpretation.

## Model Choice

The preferred Slovenian CPU-friendly candidate remains `cjvt/GaMS-1B-Chat` once it is served through Open WebUI or another compatible endpoint. It was not present in the discovered local model list during the 2026-05-21 verification run, so the current best runnable model is `ul-fri-nlp-course-project-optimized:latest` on the remote Ollama endpoint. `mistral:7b`, `llama3:latest`, and `gemma3:4b` are kept as comparison/fallback models.

The final assistant behavior is controlled mainly by `strict_legal_rag_sl_v3`: strict Slovenian answers, employment-law scope checks, source-priority rules, citation discipline, ambiguity guardrails, and refusal for unsupported questions.

The finalized Open WebUI option is `ul-fri-slovenian-employment-law-rag-openwebui` ("UL FRI Slovenian Employment Law RAG"). It wraps the best evaluated runnable base model with the selected strict prompt and deterministic settings. Refresh or recreate it with:

```bash
python evaluation/optimizations/create_ollama_model.py --verify --register-openwebui --smoke-openwebui
```

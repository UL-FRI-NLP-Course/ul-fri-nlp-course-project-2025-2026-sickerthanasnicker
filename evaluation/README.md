# Evaluation Pipeline

This directory contains a reproducible evaluation setup for the Slovenian employment-law RAG assistant.

It compares:

- `baseline`: model answers without retrieved context;
- `rag`: BM25 retrieval from `src/ul_fri_nlp/app/rag.py`, then model answers only from retrieved context;
- `arena`: the same baseline/RAG comparison across multiple configured models.

The default evaluation now uses local Ollama with `llama3:latest`. The deterministic offline mode is still available with `--provider offline`, but it is intended only as a smoke test.

## What The Evaluation Shows

The pipeline is designed to demonstrate four things:

- baseline answers are more likely to invent unsupported legal claims;
- RAG improves factual correctness by giving the model relevant legal passages;
- RAG can refuse questions whose answer is not in the corpus;
- retrieval quality affects final answer quality, so retrieval is evaluated separately from generation.

## Files

- `questions.jsonl`: 40 factual, ambiguous, and unanswerable questions.
- `config.json`: default provider/model settings and arena model list.
- `config.example.env`: example environment variables without secrets.
- `results/`: generated answer, judgement, retrieval, chart, and report snapshots.
- `fine_tuning/data/`: generated exploratory fine-tuning examples.
- `optimizations/`: static optimization configs, source manifests, prepared data, and Ollama export files.

The Python implementation lives under `src/ul_fri_nlp/`:

- `src/ul_fri_nlp/app/rag.py`: runtime retriever and CLI.
- `src/ul_fri_nlp/evaluation/`: evaluation, judging, voting, visualization, and model-provider modules.
- `src/ul_fri_nlp/optimizations/`: corpus building, source monitoring, prompt sweeps, PEFT prep, and Ollama/Open WebUI deployment helpers.
- `src/ul_fri_nlp/fine_tuning/`: exploratory grounded-data preparation.

Generated outputs are written to `evaluation/results/`.

## Configuration

The scripts load the repository-root `.env` if it exists. `.env` is ignored by git.

Example:

```bash
cp evaluation/config.example.env .env
```

Default local setup:

```bash
EVAL_PROVIDER=ollama
EVAL_MODEL=llama3:latest
JUDGE_PROVIDER=ollama
JUDGE_MODEL=llama3:latest
OLLAMA_HOST=http://localhost:11434
```

Open WebUI setup:

```bash
WEBUI_HOST=https://your-open-webui.example.com
WEBUI_API_KEY=your-api-key
```

The provider code also accepts `OLLAMA_URL`, `OPENWEBUI_URL`, and `OPENWEBUI_API_KEY` aliases, which are convenient when reusing existing local configuration.

Open WebUI support uses:

- `GET /api/models` for model discovery;
- `POST /api/chat/completions` for generation.

## Model Discovery

```bash
python -m ul_fri_nlp.evaluation.list_models --provider ollama
python -m ul_fri_nlp.evaluation.list_models --provider openwebui
```

## Run

Install dependencies if needed:

```bash
pip install -r requirements.txt
```

Run retrieval evaluation:

```bash
python -m ul_fri_nlp.evaluation.retrieval_eval
```

Rebuild the official corpus:

```bash
python -m ul_fri_nlp.optimizations.build_official_corpus \
  --output report/code/data/chunk.jsonl \
  --include-case-law \
  --max-case-law-chunks 30
```

Run default local Llama evaluation:

```bash
python -m ul_fri_nlp.evaluation.run_eval
```

Run a small quick check:

```bash
python -m ul_fri_nlp.evaluation.run_eval --limit 2
```

Run arena comparison from `config.json`:

```bash
python -m ul_fri_nlp.evaluation.run_eval --arena
```

The answer-generation, retrieval, judging, optimization, and vote scripts print CLI progress by default, including current model, question id, variant, and completed item count. Add `--quiet` to suppress progress logs.

Judge answers:

```bash
python -m ul_fri_nlp.evaluation.judge_eval
```

Generate charts and a report:

```bash
python -m ul_fri_nlp.evaluation.visualize_results
```

Run anonymized vote evaluation over an existing arena answer file:

```bash
python -m ul_fri_nlp.evaluation.vote_eval \
  --answers evaluation/results/arena_answers.jsonl \
  --output evaluation/results/vote_eval.jsonl \
  --summary-output evaluation/results/vote_summary.csv

python -m ul_fri_nlp.evaluation.visualize_results --vote-summary evaluation/results/vote_summary.csv
```

Outputs:

- `evaluation/results/answers.jsonl`
- `evaluation/results/judgements.jsonl`
- `evaluation/results/retrieval.jsonl`
- `evaluation/results/summary_scores.png`
- `evaluation/results/hallucination_by_model.png`
- `evaluation/results/refusal_accuracy.png`
- `evaluation/results/retrieval_quality.png`
- `evaluation/results/vote_eval.jsonl`
- `evaluation/results/vote_summary.csv`
- `evaluation/results/report.md`

## Arena Models

Default enabled arena models in `config.json` use the remote/local Ollama API exposed through `OLLAMA_HOST` or `OLLAMA_URL`:

- `ollama-optimized-employment-law`: `ollama / ul-fri-nlp-course-project-optimized:latest`
- `ollama-mistral-7b`: `ollama / mistral:7b`
- `ollama-llama3`: `ollama / llama3:latest`
- `ollama-gemma3-4b`: `ollama / gemma3:4b`

`qwen2.5-coder:7b` is available on the remote Ollama host but disabled by default because it was too slow for routine smoke evaluation. The requested `gpt-5.4-mini` and `gpt-5.5` entries are also written in `config.json`, but disabled by default because the current Open WebUI `/api/models` response does not expose them and direct calls returned HTTP 400. Enable disabled models only after they appear in model discovery and a short smoke run completes.

`config.json` also includes `include_raw_rag_prompt: true`, which adds a retrieval-only `raw_rag_prompt` baseline containing the exact prompt/context that would be sent to a model.

## Final Open WebUI Model

The final deployed Open WebUI option is:

- id: `ul-fri-slovenian-employment-law-rag-openwebui`
- display name: `UL FRI Slovenian Employment Law RAG`
- base model: `ul-fri-nlp-course-project-optimized:latest`
- prompt: `strict_legal_rag_sl_v3`
- settings: temperature `0.0`, top-p `1.0`, max output `500`

Refresh it with:

```bash
python -m ul_fri_nlp.optimizations.create_ollama_model --skip-create --register-openwebui --smoke-openwebui
```

The companion Ollama-only model is `ul-fri-slovenian-employment-law-rag:latest`.

Each generated answer keeps the required fields:

```json
{
  "id": "...",
  "variant": "baseline | rag",
  "question": "...",
  "context": "...",
  "answer": "..."
}
```

The upgraded pipeline also adds:

```json
{
  "model_id": "...",
  "provider": "...",
  "model": "...",
  "prompt_mode": "no_context | rag_context",
  "temperature": 0.0,
  "top_p": 1.0,
  "max_tokens": 700
}
```

## Metrics

Retrieval quality:

- hit rate for factual and ambiguous questions;
- false evidence rate for unanswerable questions;
- average context length.

Answer quality:

- correctness, grounding, completeness, clarity: 0-5 where higher is better;
- hallucination: 0-5 where lower is better;
- refusal accuracy for unanswerable questions.

## Metric Provenance

The first-order evaluation uses common RAG evaluation ideas:

- BM25 top-k retrieval over the candidate corpus;
- retrieval hit rate, analogous to recall@k on answerable questions;
- false evidence rate on unanswerable/out-of-domain questions;
- LLM-as-a-judge scoring for generated answers;
- hallucination and refusal/safety checks.

Project-specific metrics are deliberately simple and reproducible:

- `reference_keyword_fraction`: fraction of normalized reference content terms that appear in retrieved context;
- retrieval hit: `reference_keyword_fraction >= 0.35` for answerable questions;
- false evidence: the same threshold applied to unanswerable questions, where a high overlap means retrieval may mislead the generator;
- refusal accuracy: fraction of unanswerable questions where the answer contains an explicit refusal pattern;
- freshness/source availability: current reachability and validity status from `official_source_monitor.json`.

The threshold-based metrics are not a replacement for human legal review. They are used as deterministic regression checks so retrieval changes can be compared before expensive or subjective judging.

## Fine-Tuning Preparation

Prepare grounded QA data:

```bash
python -m ul_fri_nlp.fine_tuning.prepare_dataset
```

This creates:

- `evaluation/fine_tuning/data/train.jsonl`
- `evaluation/fine_tuning/data/dev.jsonl`

This step does not run expensive fine-tuning. It creates chat-style examples that can later be used for PEFT/LoRA experiments or for an Ollama Modelfile/system-prompt-tuned model.

## Correctness Optimization Track

Optimization experiments are kept separate from the main evaluation outputs:

```bash
python -m ul_fri_nlp.optimizations.build_official_corpus --include-case-law --max-case-law-chunks 30
python -m ul_fri_nlp.optimizations.run_prompt_sweep --limit 2 --provider offline
python -m ul_fri_nlp.evaluation.judge_eval \
  --answers evaluation/results/optimization/prompt_sweep_answers.jsonl \
  --output evaluation/results/optimization/judgements.jsonl
python -m ul_fri_nlp.optimizations.summarize_optimization
python -m ul_fri_nlp.optimizations.prepare_peft_dataset
python -m ul_fri_nlp.optimizations.create_ollama_model
```

See `evaluation/optimizations/README.md` for the full workflow. The queued vote-score metric plan is saved in `evaluation/backlog/vote_score_metric.md`.

Create the local optimized Ollama model:

```bash
python -m ul_fri_nlp.optimizations.create_ollama_model
ollama run ul-fri-slovenian-employment-law-rag
```

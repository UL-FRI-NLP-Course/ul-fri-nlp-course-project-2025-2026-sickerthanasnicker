# Evaluation Pipeline

This directory contains a reproducible evaluation setup for the Slovenian employment-law RAG assistant.

It compares:

- `baseline`: model answers without retrieved context;
- `rag`: BM25 retrieval from `report/code/rag.py`, then model answers only from retrieved context;
- `arena`: the same baseline/RAG comparison across multiple configured models.

The default evaluation now uses local Ollama with `llama3:latest`. The deterministic offline mode is still available with `--provider offline`, but it is intended only as a smoke test.

## What The Evaluation Shows

The pipeline is designed to demonstrate four things:

- baseline answers are more likely to invent unsupported legal claims;
- RAG improves factual correctness by giving the model relevant legal passages;
- RAG can refuse questions whose answer is not in the corpus;
- retrieval quality affects final answer quality, so retrieval is evaluated separately from generation.

## Files

- `questions.jsonl`: 20 factual, ambiguous, and unanswerable questions.
- `config.json`: default provider/model settings and arena model list.
- `config.example.env`: example environment variables without secrets.
- `list_models.py`: lists Ollama or Open WebUI models.
- `run_eval.py`: runs baseline/RAG answer generation.
- `retrieval_eval.py`: evaluates retrieval independently.
- `judge_eval.py`: scores answers and prints aggregate results.
- `visualize_results.py`: creates charts and a Markdown report.
- `fine_tuning/prepare_dataset.py`: prepares grounded QA JSONL for later fine-tuning.

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

Open WebUI support uses:

- `GET /api/models` for model discovery;
- `POST /api/chat/completions` for generation.

## Model Discovery

```bash
python evaluation/list_models.py --provider ollama
python evaluation/list_models.py --provider openwebui
```

## Run

Install dependencies if needed:

```bash
pip install rank-bm25 matplotlib python-dotenv
```

Run retrieval evaluation:

```bash
python evaluation/retrieval_eval.py
```

Run default local Llama evaluation:

```bash
python evaluation/run_eval.py
```

Run a small quick check:

```bash
python evaluation/run_eval.py --limit 2
```

Run arena comparison from `config.json`:

```bash
python evaluation/run_eval.py --arena
```

Judge answers:

```bash
python evaluation/judge_eval.py
```

Generate charts and a report:

```bash
python evaluation/visualize_results.py
```

Outputs:

- `evaluation/results/answers.jsonl`
- `evaluation/results/judgements.jsonl`
- `evaluation/results/retrieval.jsonl`
- `evaluation/results/summary_scores.png`
- `evaluation/results/hallucination_by_model.png`
- `evaluation/results/refusal_accuracy.png`
- `evaluation/results/retrieval_quality.png`
- `evaluation/results/report.md`

## Arena Models

Default arena models in `config.json`:

- `ollama-llama3`: `ollama / llama3:latest`
- `ollama-mistral`: `ollama / mistral:7b`
- `webui-project`: `openwebui / ul-fri-nlp-course-project-eal`

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

## Fine-Tuning Preparation

Prepare grounded QA data:

```bash
python evaluation/fine_tuning/prepare_dataset.py
```

This creates:

- `evaluation/fine_tuning/data/train.jsonl`
- `evaluation/fine_tuning/data/dev.jsonl`

This step does not run expensive fine-tuning. It creates chat-style examples that can later be used for PEFT/LoRA experiments or for an Ollama Modelfile/system-prompt-tuned model.

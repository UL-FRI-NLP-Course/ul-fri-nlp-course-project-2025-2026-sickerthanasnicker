# Correctness Optimization Track

This directory contains experiments that are separate from the main reproducible evaluation in `evaluation/`.
The goal is to improve answer correctness while preserving grounding and refusal behavior.

## 1. Prepare Shared Corpus Chunks

The COLESLAW archive is streamed directly from `corpus/COLESLAW.zip`; it is not extracted into the repository.

```bash
python evaluation/optimizations/prepare_corpus.py --limit 500
```

Outputs:

- `evaluation/optimizations/data/coleslaw_employment_chunks.jsonl`
- `evaluation/optimizations/data/coleslaw_employment_summary.json`

These normalized chunks can be reused for retrieval experiments and fine-tuning data preparation.

For a bounded fuller local preparation run with progress:

```bash
python evaluation/optimizations/prepare_corpus.py \
  --limit 500 \
  --max-records 50000 \
  --progress-every 5000
```

## 2. Run Prompt And Parameter Sweep

Smoke test without live model calls:

```bash
python evaluation/optimizations/run_prompt_sweep.py --limit 2 --provider offline
```

Run configured Open WebUI models:

```bash
python evaluation/optimizations/run_prompt_sweep.py --limit 2
```

The sweep prints current model, prompt, parameter set, question id, variant, and total progress. Use `--quiet` only when logging is too noisy.

To reduce runtime, filter to one model, prompt, or parameter set:

```bash
python evaluation/optimizations/run_prompt_sweep.py \
  --model-id webui-mistral-7b \
  --prompt-id strict_grounded_v1 \
  --settings-id deterministic
```

Outputs:

- `evaluation/results/optimization/prompt_sweep_answers.jsonl`
- `evaluation/results/optimization/retrieval.jsonl`

## 3. Judge And Report

Use the existing judge, but write to the optimization results folder:

```bash
python evaluation/judge_eval.py \
  --answers evaluation/results/optimization/prompt_sweep_answers.jsonl \
  --output evaluation/results/optimization/judgements.jsonl

python evaluation/optimizations/summarize_optimization.py
```

Outputs:

- `evaluation/results/optimization/optimization_report.md`
- `evaluation/results/optimization/optimization_summary.csv`
- `evaluation/results/optimization/optimization_correctness.png`
- `evaluation/results/optimization/optimization_hallucination.png`
- `evaluation/results/optimization/optimization_refusal_accuracy.png`

## 4. Prepare PEFT Dataset

This does not run training. It prepares chat-style JSONL for later LoRA/PEFT.

```bash
python evaluation/optimizations/prepare_peft_dataset.py
```

Outputs:

- `evaluation/optimizations/data/peft_train.jsonl`
- `evaluation/optimizations/data/peft_dev.jsonl`

Default PEFT target is Mistral 7B because it is the local model most likely to benefit from task-specific adaptation. On the discovered local hardware, full training should be done in Colab/Kaggle or another GPU environment with current `torch`, `transformers`, `datasets`, `peft`, `trl`, and `accelerate`.

The current prepared dataset can be regenerated with more corpus examples:

```bash
python evaluation/optimizations/prepare_peft_dataset.py --max-corpus-examples 200
```

## 5. Export Open WebUI Preset

This creates files for a usable Open WebUI model/preset. It does not mutate Open WebUI by default.

```bash
python evaluation/optimizations/export_webui_model.py
```

Outputs:

- `evaluation/optimizations/webui/optimized_model_preset.json`
- `evaluation/optimizations/webui/openwebui_create_model_payload.json`

If your Open WebUI instance exposes the model creation API and your API key has permission, creation can be attempted explicitly:

```bash
python evaluation/optimizations/export_webui_model.py --create
```

## 6. Create Local Ollama Model

Create the local optimized model from `mistral:7b`, the selected system prompt, deterministic parameters, and grounded examples:

```bash
python evaluation/optimizations/create_ollama_model.py
```

Run it directly:

```bash
ollama run ul-fri-nlp-course-project-optimized
```

Evaluate it through the main pipeline:

```bash
python evaluation/run_eval.py \
  --provider ollama \
  --model ul-fri-nlp-course-project-optimized:latest \
  --output evaluation/results/optimized_ollama_answers.jsonl
```

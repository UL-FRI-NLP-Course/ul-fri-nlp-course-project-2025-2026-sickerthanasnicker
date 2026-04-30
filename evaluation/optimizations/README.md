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

## 2. Run Prompt And Parameter Sweep

Smoke test without live model calls:

```bash
python evaluation/optimizations/run_prompt_sweep.py --limit 2 --provider offline
```

Run configured Open WebUI models:

```bash
python evaluation/optimizations/run_prompt_sweep.py --limit 2
```

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


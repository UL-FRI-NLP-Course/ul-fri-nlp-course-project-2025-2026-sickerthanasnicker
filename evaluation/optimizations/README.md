# Correctness Optimization Track

This directory contains experiments that are separate from the main reproducible evaluation in `evaluation/`.
The goal is to improve answer correctness while preserving grounding and refusal behavior.

## 1. Build Official Corpus

The final RAG corpus is built from current official sources plus a bounded tertiary case-law tier:

```bash
python -m ul_fri_nlp.optimizations.build_official_corpus \
  --output report/code/data/chunk.jsonl \
  --include-case-law \
  --max-case-law-chunks 30
```

Outputs:

- `report/code/data/chunk.jsonl`
- `evaluation/optimizations/data/official_employment_summary.json`

The current committed corpus has 1,371 chunks: PISRS article-level law chunks, official interpretation/guidance chunks, and 30 tertiary COLESLAW/sodnapraksa chunks.

## 1b. Prepare COLESLAW Case-Law Chunks

The COLESLAW archive is streamed directly from `corpus/COLESLAW.zip`; it is not extracted into the repository.

```bash
python -m ul_fri_nlp.optimizations.prepare_corpus --limit 500
```

Outputs:

- `evaluation/optimizations/data/coleslaw_employment_chunks.jsonl`
- `evaluation/optimizations/data/coleslaw_employment_summary.json`

These normalized chunks can be reused for retrieval experiments and fine-tuning data preparation.
The current extraction is useful as case-law and tertiary support, but it should not be treated as the primary RAG corpus because it is dominated by `SodnaPraksa/sp_courts.jsonl` and one sector-specific collective agreement.

For a bounded fuller local preparation run with progress:

```bash
python -m ul_fri_nlp.optimizations.prepare_corpus \
  --limit 500 \
  --max-records 50000 \
  --progress-every 5000
```

## 1c. Monitor Official Sources

Official primary and interpretation sources are tracked in:

- `evaluation/optimizations/official_sources.json`

Run the monitor:

```bash
python -m ul_fri_nlp.optimizations.monitor_official_sources
```

Output:

- `evaluation/results/optimization/official_source_monitor.json`

The monitor checks PISRS register matches and GOV.SI/MDDSZ/ZZZS/IRSD/eUprava/SPOT/ESS/OPSI source availability, including selected DOCX/PDF explanation files. The current final-submission snapshot reports 12/12 PISRS sources, 24/24 government/official interpretation or operational sources, and 1/1 case-law source reachable. Use this before rebuilding the official RAG corpus or reporting current-law results.

## 2. Run Prompt And Parameter Sweep

Smoke test without live model calls:

```bash
python -m ul_fri_nlp.optimizations.run_prompt_sweep --limit 2 --provider offline
```

Run configured live models:

```bash
python -m ul_fri_nlp.optimizations.run_prompt_sweep --limit 2
```

The sweep prints current model, prompt, parameter set, question id, variant, and total progress. Use `--quiet` only when logging is too noisy.

To reduce runtime, filter to one model, prompt, or parameter set:

```bash
python -m ul_fri_nlp.optimizations.run_prompt_sweep \
  --model-id webui-mistral-7b \
  --prompt-id strict_legal_rag_sl_v2 \
  --settings-id deterministic
```

Outputs:

- `evaluation/results/optimization/prompt_sweep_answers.jsonl`
- `evaluation/results/optimization/retrieval.jsonl`

## 3. Judge And Report

Use the existing judge, but write to the optimization results folder:

```bash
python -m ul_fri_nlp.evaluation.judge_eval \
  --answers evaluation/results/optimization/prompt_sweep_answers.jsonl \
  --output evaluation/results/optimization/judgements.jsonl

python -m ul_fri_nlp.optimizations.summarize_optimization
```

Outputs:

- `evaluation/results/optimization/optimization_report.md`
- `evaluation/results/optimization/optimization_summary.csv`
- `evaluation/results/optimization/optimization_correctness.png`
- `evaluation/results/optimization/optimization_hallucination.png`
- `evaluation/results/optimization/optimization_refusal_accuracy.png`

## 4. Prepare PEFT Dataset

This does not run training. It prepares chat-style JSONL for later LoRA/PEFT. For the final submission this is exploratory only and is not part of the selected approach; regenerate the data before using it because the final model choice is RAG-only.

```bash
python -m ul_fri_nlp.optimizations.prepare_peft_dataset
```

Outputs:

- `evaluation/optimizations/data/peft_train.jsonl`
- `evaluation/optimizations/data/peft_dev.jsonl`

Default PEFT target is Mistral 7B because it is the local model most likely to benefit from task-specific adaptation. On the discovered local hardware, full training should be done in Colab/Kaggle or another GPU environment with current `torch`, `transformers`, `datasets`, `peft`, `trl`, and `accelerate`.

The current prepared dataset can be regenerated with more corpus examples:

```bash
python -m ul_fri_nlp.optimizations.prepare_peft_dataset --max-corpus-examples 200
```

## 5. Create Local Ollama Model

Create the local optimized model from the configured base model, selected system prompt, deterministic parameters, and optional grounded examples:

```bash
python -m ul_fri_nlp.optimizations.create_ollama_model
```

Run it directly:

```bash
ollama run ul-fri-slovenian-employment-law-rag
```

Register or refresh the final Open WebUI model wrapper:

```bash
python -m ul_fri_nlp.optimizations.create_ollama_model \
  --skip-create \
  --register-openwebui \
  --smoke-openwebui
```

Evaluate it through the main pipeline:

```bash
python -m ul_fri_nlp.evaluation.run_eval \
  --provider ollama \
  --model ul-fri-slovenian-employment-law-rag:latest \
  --output evaluation/results/optimized_ollama_answers.jsonl
```

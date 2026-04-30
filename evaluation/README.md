# Evaluation Pipeline

This directory contains a reproducible evaluation setup for the Slovenian legal RAG assistant.
It compares:

- `baseline`: answers the question without retrieved context.
- `rag`: retrieves legal passages with the existing BM25 search code from `report/code/rag.py` and answers only from that context.
- `slovenian`: optional extra model variant, enabled only when a Slovenian model is configured.

The checked-in project currently contains retrieval but no production LLM call. For reproducibility, the scripts therefore support two modes:

- offline fallback mode, which is deterministic and needs no API key;
- real LLM mode through OpenAI or Ollama, configured with environment variables.

## Files

- `questions.jsonl`: 20 evaluation questions split into factual, ambiguous, and unanswerable cases.
- `run_eval.py`: runs baseline and RAG answer generation.
- `retrieval_eval.py`: evaluates retrieval independently from answer generation.
- `judge_eval.py`: evaluates answers and aggregates results.

Generated outputs are written to `evaluation/results/`.

## Run

Install the retrieval dependency if needed:

```bash
pip install rank-bm25
```

Run retrieval evaluation:

```bash
python evaluation/retrieval_eval.py
```

Run answer generation:

```bash
python evaluation/run_eval.py
```

Judge answers and print the summary table:

```bash
python evaluation/judge_eval.py
```

## Optional LLM Providers

OpenAI:

```bash
export EVAL_PROVIDER=openai
export EVAL_MODEL=<model-name>
export OPENAI_API_KEY=<api-key>
python evaluation/run_eval.py
python evaluation/judge_eval.py
```

Ollama:

```bash
export EVAL_PROVIDER=ollama
export EVAL_MODEL=<ollama-model>
python evaluation/run_eval.py
python evaluation/judge_eval.py
```

Optional Slovenian model:

```bash
export SLOVENIAN_MODEL=<model-name>
python evaluation/run_eval.py
```

## Metrics

Retrieval quality is measured before generation:

- hit rate: for factual and ambiguous questions, whether reference keywords appear in the retrieved top-k context;
- unanswerable false evidence rate: how often retrieved context looks like it contains evidence for unanswerable questions;
- average context length: average number of retrieved context words.

Answer quality is measured per system:

- correctness, grounding, completeness, and clarity are scored from 0 to 5, where higher is better;
- hallucination is scored from 0 to 5, where lower is better;
- refusal accuracy measures whether the model refuses unanswerable questions.

The RAG prompt requires the model to answer only from retrieved context. This should improve factual correctness, reduce unsupported claims, and make unanswerable questions easier to reject. The final answer quality still depends on retrieval: if the right passage is not retrieved, the generator cannot reliably produce a grounded answer.

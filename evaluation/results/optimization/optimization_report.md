# Correctness Optimization Results

These results are separate from the main reproducible evaluation. They compare system prompts and generation settings for model optimization.

## Best RAG Configurations

| model_id | variant | prompt_id | settings_id | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| offline-webui-mistral-7b | rag | strict_legal_rag_sl_v2 | deterministic | 20 | 1.85 | 4.25 | 1.85 | 5.00 | 1.80 | 1.00 |

## Full Summary

| model_id | variant | prompt_id | settings_id | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| offline-webui-mistral-7b | baseline | strict_legal_rag_sl_v2 | deterministic | 20 | 0.70 | 0.20 | 0.70 | 5.00 | 4.20 | 0.00 |
| offline-webui-mistral-7b | rag | strict_legal_rag_sl_v2 | deterministic | 20 | 1.85 | 4.25 | 1.85 | 5.00 | 1.80 | 1.00 |

## Retrieval

- Answerable hit rate: 0.500
- Unanswerable false evidence rate: 0.250
- Average context length: 557.2 words

## Charts

Charts were skipped because `matplotlib` is not installed in this environment.


CSV tables:

- [optimization_summary.csv](optimization_summary.csv)
- [optimization_retrieval_summary.csv](optimization_retrieval_summary.csv)

# Correctness Optimization Results

These results are separate from the main reproducible evaluation. They compare system prompts and generation settings for model optimization.

## Best RAG Configurations

| model_id | variant | prompt_id | settings_id | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| offline-webui-mistral-7b | rag | strict_legal_rag_sl_v3 | deterministic | 20 | 3.15 | 3.75 | 3.15 | 5.00 | 0.85 | 1.00 |

## Full Summary

| model_id | variant | prompt_id | settings_id | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| offline-webui-mistral-7b | baseline | strict_legal_rag_sl_v3 | deterministic | 20 | 0.70 | 0.20 | 0.70 | 5.00 | 4.20 | 0.00 |
| offline-webui-mistral-7b | rag | strict_legal_rag_sl_v3 | deterministic | 20 | 3.15 | 3.75 | 3.15 | 5.00 | 0.85 | 1.00 |

## Retrieval

- Answerable hit rate: 1.000
- Unanswerable false evidence rate: 0.000
- Average context length: 200.4 words

## Charts

![Correctness](optimization_correctness.png)

![Hallucination](optimization_hallucination.png)

![Refusal accuracy](optimization_refusal_accuracy.png)


CSV tables:

- [optimization_summary.csv](optimization_summary.csv)
- [optimization_retrieval_summary.csv](optimization_retrieval_summary.csv)

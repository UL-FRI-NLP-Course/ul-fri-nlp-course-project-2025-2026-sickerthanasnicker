# Correctness Optimization Results

These results are separate from the main reproducible evaluation. They compare system prompts and generation settings for model optimization.

## Best RAG Configurations

| model_id | variant | prompt_id | settings_id | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| offline-webui-mistral-7b | rag | ambiguity_aware_v1 | deterministic | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-mistral-7b | rag | ambiguity_aware_v1 | focused | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-mistral-7b | rag | citation_first_v1 | deterministic | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-mistral-7b | rag | citation_first_v1 | focused | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-mistral-7b | rag | strict_grounded_v1 | deterministic | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |

## Full Summary

| model_id | variant | prompt_id | settings_id | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| offline-webui-mistral-7b | baseline | ambiguity_aware_v1 | deterministic | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-mistral-7b | baseline | ambiguity_aware_v1 | focused | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-mistral-7b | baseline | citation_first_v1 | deterministic | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-mistral-7b | baseline | citation_first_v1 | focused | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-mistral-7b | baseline | strict_grounded_v1 | deterministic | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-mistral-7b | baseline | strict_grounded_v1 | focused | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-mistral-7b | rag | ambiguity_aware_v1 | deterministic | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-mistral-7b | rag | ambiguity_aware_v1 | focused | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-mistral-7b | rag | citation_first_v1 | deterministic | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-mistral-7b | rag | citation_first_v1 | focused | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-mistral-7b | rag | strict_grounded_v1 | deterministic | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-mistral-7b | rag | strict_grounded_v1 | focused | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | baseline | ambiguity_aware_v1 | deterministic | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | baseline | ambiguity_aware_v1 | focused | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | baseline | citation_first_v1 | deterministic | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | baseline | citation_first_v1 | focused | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | baseline | strict_grounded_v1 | deterministic | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | baseline | strict_grounded_v1 | focused | 2 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | rag | ambiguity_aware_v1 | deterministic | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | rag | ambiguity_aware_v1 | focused | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | rag | citation_first_v1 | deterministic | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | rag | citation_first_v1 | focused | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | rag | strict_grounded_v1 | deterministic | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |
| offline-webui-qwen3-coder-30b-a3b | rag | strict_grounded_v1 | focused | 2 | 2.00 | 5.00 | 2.00 | 5.00 | 3.00 | 0.00 |

## Retrieval

- Answerable hit rate: 1.000
- Unanswerable false evidence rate: 0.000
- Average context length: 562.0 words

## Charts

![Correctness](optimization_correctness.png)

![Hallucination](optimization_hallucination.png)

![Refusal accuracy](optimization_refusal_accuracy.png)

CSV tables:

- [optimization_summary.csv](optimization_summary.csv)
- [optimization_retrieval_summary.csv](optimization_retrieval_summary.csv)

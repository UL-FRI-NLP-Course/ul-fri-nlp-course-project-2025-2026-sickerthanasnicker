# Evaluation Results

## Answer Scores

| model_id | model_label | variant | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| offline-llama3:latest | offline-llama3:latest | baseline | 20 | 0.70 | 0.20 | 0.70 | 5.00 | 4.20 | 0.00 |
| offline-llama3:latest | offline-llama3:latest | rag | 20 | 3.20 | 3.70 | 3.20 | 5.00 | 0.85 | 1.00 |
| raw-rag-prompt | raw RAG prompt | raw_rag_prompt | 20 | 1.80 | 4.80 | 1.80 | 3.10 | 0.00 | 1.00 |

## Retrieval

- Answerable hit rate: 0.938
- Unanswerable false evidence rate: 0.000
- Average context length: 191.8 words


## Charts

Charts were skipped because `matplotlib` is not installed in this environment.


CSV tables:

- [summary_scores.csv](summary_scores.csv)
- [retrieval_summary.csv](retrieval_summary.csv)

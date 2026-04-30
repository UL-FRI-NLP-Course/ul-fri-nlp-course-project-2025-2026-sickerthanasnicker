# Evaluation Results

## Answer Scores

| model_id | variant | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ollama-llama3:latest | baseline | 2 | 5.00 | 5.00 | 5.00 | 5.00 | 0.00 | 0.00 |
| ollama-llama3:latest | rag | 2 | 5.00 | 5.00 | 5.00 | 5.00 | 0.00 | 0.00 |

## Retrieval

- Answerable hit rate: 0.875
- Unanswerable false evidence rate: 0.250
- Average context length: 176.3 words

## Charts

![Summary scores](summary_scores.png)

![Hallucination by model](hallucination_by_model.png)

![Refusal accuracy](refusal_accuracy.png)

![Retrieval quality](retrieval_quality.png)

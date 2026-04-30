# Evaluation Results

## Answer Scores

| model_id | variant | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ollama-llama3:latest | baseline | 20 | 4.15 | 4.75 | 4.70 | 4.95 | 1.00 | 0.00 |
| ollama-llama3:latest | rag | 20 | 3.85 | 4.95 | 4.55 | 4.85 | 0.25 | 0.75 |

## Retrieval

- Answerable hit rate: 0.875
- Unanswerable false evidence rate: 0.250
- Average context length: 176.3 words

## Charts

![Summary scores](summary_scores.png)

SVG: [summary_scores.svg](summary_scores.svg)
JPG: [summary_scores.jpg](summary_scores.jpg)

![Hallucination by model](hallucination_by_model.png)

SVG: [hallucination_by_model.svg](hallucination_by_model.svg)
JPG: [hallucination_by_model.jpg](hallucination_by_model.jpg)

![Refusal accuracy](refusal_accuracy.png)

SVG: [refusal_accuracy.svg](refusal_accuracy.svg)
JPG: [refusal_accuracy.jpg](refusal_accuracy.jpg)

![Retrieval quality](retrieval_quality.png)

SVG: [retrieval_quality.svg](retrieval_quality.svg)
JPG: [retrieval_quality.jpg](retrieval_quality.jpg)

CSV tables:

- [summary_scores.csv](summary_scores.csv)
- [retrieval_summary.csv](retrieval_summary.csv)

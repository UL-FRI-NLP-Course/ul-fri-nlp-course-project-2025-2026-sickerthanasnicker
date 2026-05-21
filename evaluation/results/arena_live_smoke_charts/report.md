# Evaluation Results

## Answer Scores

| model_id | model_label | variant | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ollama-gemma3-4b | gemma3:4b | baseline | 5 | 4.20 | 4.40 | 5.00 | 4.40 | 1.00 | 0.00 |
| ollama-gemma3-4b | gemma3:4b | rag | 5 | 5.00 | 5.00 | 5.00 | 5.00 | 0.00 | 0.00 |
| ollama-llama3 | llama3:latest | baseline | 5 | 4.20 | 4.40 | 4.80 | 5.00 | 0.00 | 0.00 |
| ollama-llama3 | llama3:latest | rag | 5 | 5.00 | 5.00 | 5.00 | 5.00 | 0.00 | 0.00 |
| ollama-mistral-7b | mistral:7b | baseline | 5 | 4.20 | 5.00 | 4.80 | 4.40 | 0.00 | 0.00 |
| ollama-mistral-7b | mistral:7b | rag | 5 | 5.00 | 5.00 | 5.00 | 4.80 | 0.00 | 0.00 |
| ollama-optimized-employment-law | optimized employment-law mistral | baseline | 5 | 4.40 | 5.00 | 4.40 | 4.80 | 0.00 | 0.00 |
| ollama-optimized-employment-law | optimized employment-law mistral | rag | 5 | 5.00 | 5.00 | 5.00 | 4.80 | 0.00 | 0.00 |
| raw-rag-prompt | raw RAG prompt | raw_rag_prompt | 5 | 5.00 | 5.00 | 5.00 | 5.00 | 0.00 | 0.00 |

## Retrieval

- Answerable hit rate: 1.000
- Unanswerable false evidence rate: 0.000
- Average context length: 189.9 words


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

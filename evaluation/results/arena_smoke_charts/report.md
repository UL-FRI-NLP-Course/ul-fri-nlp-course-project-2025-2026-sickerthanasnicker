# Evaluation Results

## Answer Scores

| model_id | model_label | variant | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| raw-rag-prompt | raw RAG prompt | raw_rag_prompt | 1 | 1.00 | 5.00 | 1.00 | 3.00 | 0.00 | 0.00 |
| webui-llama3 | llama3:latest | baseline | 1 | 1.00 | 0.00 | 1.00 | 5.00 | 4.00 | 0.00 |
| webui-llama3 | llama3:latest | rag | 1 | 3.00 | 2.00 | 3.00 | 5.00 | 2.00 | 0.00 |
| webui-mistral-7b | mistral:7b | baseline | 1 | 2.00 | 0.00 | 2.00 | 5.00 | 4.00 | 0.00 |
| webui-mistral-7b | mistral:7b | rag | 1 | 3.00 | 4.00 | 3.00 | 5.00 | 2.00 | 0.00 |
| webui-qwen2.5-coder-7b | qwen2.5-coder:7b | baseline | 1 | 2.00 | 0.00 | 2.00 | 5.00 | 4.00 | 0.00 |
| webui-qwen2.5-coder-7b | qwen2.5-coder:7b | rag | 1 | 3.00 | 5.00 | 3.00 | 5.00 | 2.00 | 0.00 |
| webui-qwen3-coder-30b-a3b | qwen3-Coder30B-A3B-Instruct | baseline | 1 | 3.00 | 0.00 | 3.00 | 5.00 | 2.00 | 0.00 |
| webui-qwen3-coder-30b-a3b | qwen3-Coder30B-A3B-Instruct | rag | 1 | 3.00 | 4.00 | 3.00 | 5.00 | 2.00 | 0.00 |

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

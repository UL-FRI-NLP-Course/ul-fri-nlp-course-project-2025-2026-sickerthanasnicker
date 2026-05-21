# Evaluation Results

## Answer Scores

| model_id | model_label | variant | n | correctness | grounding | completeness | clarity | hallucination | refusal_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openwebui-ul-fri-slovenian-employment-law-rag-openwebui | openwebui-ul-fri-slovenian-employment-law-rag-openwebui | baseline | 20 | 1.85 | 1.00 | 1.85 | 5.00 | 0.20 | 1.00 |
| openwebui-ul-fri-slovenian-employment-law-rag-openwebui | openwebui-ul-fri-slovenian-employment-law-rag-openwebui | rag | 20 | 2.85 | 3.95 | 2.85 | 5.00 | 0.75 | 1.00 |
| raw-rag-prompt | raw RAG prompt | raw_rag_prompt | 20 | 1.80 | 4.90 | 1.80 | 3.10 | 0.00 | 1.00 |

## Retrieval

- Answerable hit rate: 1.000
- Unanswerable false evidence rate: 0.000
- Average context length: 200.4 words


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

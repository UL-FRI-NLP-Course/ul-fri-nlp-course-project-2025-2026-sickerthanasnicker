# Standalone App Plan

This project currently prioritizes the NLP pipeline, source curation, and evaluation. A standalone app is planned as a deployment layer, not as evidence for the core final result.

## Recommended Direction

Build a small Progressive Web App first.

Reasons:

- it can run anywhere with a browser and does not require app-store packaging;
- it can call the existing Open WebUI or Ollama-compatible backend;
- it keeps the legal assistant UI simple: question input, answer, refusal state, citations, and retrieved sources;
- it is easier for peer reviewers to run than a desktop or mobile package.

Tauri is a reasonable later option if an offline desktop package becomes important. Flutter is a larger investment and only makes sense if the project becomes mobile-first.

## Minimal App Features

- Slovenian question input with a clear employment-law scope label.
- Answer panel with the model response.
- Source panel showing retrieved law/article/source metadata for every non-refusal answer.
- Explicit refusal state for out-of-scope or unsupported questions.
- Copyable citation text.
- Debug view for retrieved chunks, BM25 scores, prompt id, model id, and timestamp.

## Backend Contract

The app should use the existing RAG pipeline rather than duplicating logic.

Suggested response shape:

```json
{
  "question": "...",
  "answer": "...",
  "refused": false,
  "model_id": "ul-fri-slovenian-employment-law-rag-openwebui",
  "prompt_id": "strict_legal_rag_sl_v3",
  "sources": [
    {
      "law": "ZDR-1",
      "article": "159-161",
      "source": "PISRS",
      "score": 12.4,
      "text": "..."
    }
  ]
}
```

## Implementation Phases

1. Wrap `evaluation/retrieval_shared.py` and the selected model provider in a small HTTP API.
2. Add citation validation before returning a supported answer.
3. Build the PWA UI with answer, citations, retrieved evidence, and error states.
4. Add regression tests using `evaluation/questions.jsonl`.
5. Only then package with Tauri if offline desktop distribution is needed.

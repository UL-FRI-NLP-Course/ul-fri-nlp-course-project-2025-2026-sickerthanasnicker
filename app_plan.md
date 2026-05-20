# Slovenian Employment-Law Assistant App Plan

## Goal

Build a standalone Slovenian legal assistant that replaces the Open WebUI interface for this project. The app should answer questions about Slovenian employment law, cite official sources, accept legal documents as attachments, and refuse every question that is not about Slovenian employment law or is not supported by the indexed corpus.

This is a RAG-first app. No fine-tuning is planned unless retrieval, chunking, prompting, and model selection have already been exhausted.

## Product Scope

Core user flows:

- ask a Slovenian employment-law question in Slovenian;
- receive a short answer with cited sources and relevant article numbers;
- see which retrieved sources were used;
- attach a PDF, DOCX, image, or screenshot for interpretation;
- ask follow-up questions about the uploaded document;
- get a refusal for tax, inheritance, company formation, criminal, foreign-law, or general HR questions outside Slovenian employment law.

The app should not present itself as a lawyer. It should explain that answers are informational, grounded in official sources, and may require a qualified legal professional for action.

## System Architecture

Recommended architecture:

- frontend: custom chat UI;
- backend API: document upload, OCR/text extraction, retrieval, model orchestration, audit logging;
- vector/lexical store: hybrid retrieval with metadata filters;
- model runtime: local Open WebUI/Ollama-compatible endpoint at first, later a direct Hugging Face/Transformers service if needed;
- corpus monitor: scheduled run of `evaluation/optimizations/monitor_official_sources.py`;
- admin view: corpus freshness, failed sources, evaluation scores, prompt version.

Answer pipeline:

1. Classify scope: Slovenian employment law or refuse.
2. Extract user facts and legal issue.
3. Retrieve official sources.
4. Rerank by source priority: PISRS, official interpretations, then case law.
5. Generate answer with `strict_legal_rag_sl_v2`.
6. Verify citations and refuse if support is weak.
7. Return answer, citations, and confidence/freshness notes.

## Corpus Design

Primary corpus:

- PISRS statutes from `evaluation/optimizations/official_sources.json`;
- chunk at article/subarticle level;
- metadata: source type, law short name, article, title, PISRS ID, SOP, NPB version, validity status, URL, retrieved date.

Secondary corpus:

- GOV.SI, MDDSZ, IRSD, eUprava, SPOT, ESS official guidance;
- chunk by page section;
- metadata: institution, page title, heading path, publication/update date when available.

Tertiary corpus:

- `sodnapraksa.si` and selected COLESLAW case-law chunks;
- used for demo examples and interpretation support only;
- never outranks a current statute.

Uploaded documents:

- separate temporary per-user index;
- extracted text should be cited as `uploaded_document`;
- the model must distinguish uploaded document content from official law.

## Model Plan

Preferred model path:

- `cjvt/GaMS-1B-Chat` from Hugging Face as the CPU-friendly Slovenian answer model;
- `cjvt/GaMS-9B` only if hardware allows;
- `mistral:7b` remains the current fallback.

Generation settings:

- temperature `0.0`;
- top-p `1.0`;
- deterministic seed where supported;
- short answers by default;
- refusal-first prompt for unsupported questions.

Embeddings/reranking:

- start with BM25 or the existing lexical fallback for reproducibility;
- add Slovenian/multilingual embeddings only after the official corpus is clean;
- add a lightweight reranker if CPU latency remains acceptable.

## Evaluation Plan

Retrieval:

- answerable hit rate;
- unanswerable false evidence rate;
- average context length;
- source-priority accuracy;
- freshness and validity status.

Answer quality:

- correctness, grounding, completeness, clarity;
- hallucination score;
- refusal accuracy;
- citation precision;
- article exactness;
- temporal correctness for changing values such as minimum wage.

Document analysis:

- text extraction success rate;
- OCR success rate for screenshots/scans;
- citation separation between uploaded document and official law;
- refusal when the uploaded document asks for non-employment-law analysis.

Human legal review:

- sample every evaluation release;
- mark false citations, outdated rules, missing conditions, and overconfident advice.

## Refusal Policy

Refuse when:

- the question is not about Slovenian employment law;
- the user asks about another country’s employment law;
- the retrieved context does not support the answer;
- the user asks for tax, inheritance, company registration, criminal, family, immigration-only, or general business law unless it directly intersects with Slovenian employment law;
- the user asks the app to draft deceptive or unlawful conduct.

Refusal shape:

> Iz podanega konteksta ni mogoče zanesljivo odgovoriti na vprašanje iz slovenskega delovnega prava.

The app may add one short sentence naming the missing source or explaining the scope boundary.

## Platform Options

| Option | Pros | Cons | Fit |
| --- | --- | --- | --- |
| PWA / web app | Fastest to build, easiest deployment, works on desktop and mobile, best fit for backend-heavy RAG, simple auth and file upload | Less native desktop integration, offline support needs extra work | Best first version |
| Tauri | Lightweight desktop app, good file-system integration, can bundle a local UI, smaller than Electron | More packaging complexity, desktop-first, mobile story weaker | Good later if local/offline desktop is required |
| Flutter | Strong cross-platform UI, good mobile and desktop reach, polished native-feeling controls | More work for web-style document workflows, harder to iterate with existing Python/RAG backend, larger app surface | Good only if mobile-first becomes a hard requirement |

Recommendation: build a PWA first. It best matches a RAG backend, file uploads, admin monitoring, and course-project speed. Add Tauri later if the app must run as a local desktop client around a local model. Use Flutter only if mobile-native distribution becomes the main goal.

## Implementation Phases

Phase 1: Corpus and evaluation foundation

- finalize official source ingestion;
- build article-level PISRS chunks;
- separate primary, secondary, and case-law indexes;
- expand evaluation set and run prompt/model sweeps.

Phase 2: Backend API

- `/chat`;
- `/upload`;
- `/documents/{id}/chunks`;
- `/sources/status`;
- `/eval/latest`;
- persistent conversation and citation audit logs.

Phase 3: Custom chat UI

- source-cited answer cards;
- attachment panel;
- source inspector;
- refusal state;
- feedback buttons for wrong answer, stale law, missing citation.

Phase 4: Quality gates

- automated retrieval regression;
- citation validation;
- source freshness check before answer generation;
- human review export.

Phase 5: Packaging

- deploy PWA;
- optional Tauri wrapper for local desktop use;
- document model setup for GaMS/Open WebUI/Ollama-compatible runtime.

## Risks

- PISRS content extraction needs stable handling of current consolidated text versions.
- Case law can be outdated or fact-specific, so it must stay secondary.
- Legal values change over time, especially minimum wage.
- Small CPU-friendly models may answer fluently but miss legal nuance; strict context and citation validation are mandatory.
- OCR can introduce errors, so uploaded images need confidence checks and user-visible extracted text.

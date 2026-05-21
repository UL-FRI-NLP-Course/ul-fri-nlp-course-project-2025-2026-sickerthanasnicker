# RAG Optimization Report

Date: 2026-05-21

## Scope Decision

The project should use one main approach: retrieval-augmented generation (RAG). This matches the lab recommendation, keeps the system understandable, and avoids expensive fine-tuning on a CPU-limited machine. Fine-tuning remains a later option only if prompt and retrieval optimization stop improving grounded correctness.

The assistant must answer only Slovenian employment-law questions, in Slovenian, and must refuse questions outside that scope or questions not supported by retrieved sources.

## Current Corpus Audit

The repository currently has two different RAG corpora:

| Corpus | Size | Main content | Current retrieval result |
| --- | ---: | --- | --- |
| `report/code/data/chunk.jsonl` | 14 chunks | Curated ZDR-1/ZMinP snippets | Answerable Hit@3 `1.000`, false evidence rate `0.000`, average context `200.4` words |
| `evaluation/optimizations/data/coleslaw_employment_chunks.jsonl` | 500 chunks | 398 `sp_courts`, 96 journalist collective agreement chunks, 6 constitutional-decision chunks | Answerable Hit@3 `0.813`, false evidence rate `0.000`, average context `555.3` words |

Conclusion: the curated corpus is small but much safer for the current test set. The COLESLAW extraction is useful for a demo case-law index, but it should not be the primary legal source because it over-retrieves old case law and sector-specific collective-agreement text.

I also corrected stale gold data in the curated corpus and evaluation set:

- annual leave is acquired when the employment relationship is concluded, with proportional leave if employment lasts less than the full calendar year;
- severance under ZDR-1 Article 108 uses service-length tiers, not an age-over-55 shortcut;
- ordinary non-work-related sick leave is employer-funded up to 20 working days per absence, not 30;
- sickness is not a blanket prohibition on every termination, but can affect the date employment ends after notice.

## Official Source Monitoring

Added and updated:

- `evaluation/optimizations/official_sources.json`
- `evaluation/optimizations/monitor_official_sources.py`
- `evaluation/results/optimization/official_source_monitor.json`

Run:

```bash
python evaluation/optimizations/monitor_official_sources.py
```

The current snapshot found `12/12` PISRS sources, `17/17` government and official interpretation sources, and `1/1` official case-law source reachable.

Primary source policy:

1. PISRS statutes and consolidated texts are canonical.
2. GOV.SI, MDDSZ, IRSD, eUprava, SPOT, and ESS pages are official explanations.
3. `sodnapraksa.si` is secondary support for examples and legal interpretation, not the first source for statutory answers.

Core official sources now tracked:

- ZDR-1, `ZAKO5944`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO5944
- ZMinP, `ZAKO5861`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO5861
- ZEPDSV, `ZAKO4400`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO4400
- ZUTD, `ZAKO5840`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO5840
- ZVZD-1, `ZAKO5537`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO5537
- ZID-1, `ZAKO6711`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO6711
- ZKolP, `ZAKO4337`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO4337
- ZSDU, `ZAKO282`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO282
- ZRSin, `ZAKO262`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO262
- ZPDPD, `ZAKO865`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO865
- ZZSDT, `ZAKO6655`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO6655
- ZJU-1, `ZAKO8830`: https://pisrs.si/Pis.web/pregledPredpisa?id=ZAKO8830

Additional monitored official support sources:

- GOV.SI employment hub: https://www.gov.si/teme/delovna-razmerja/
- GOV.SI ZDR-1 expert group page: https://www.gov.si/zbirke/delovna-telesa/strokovna-delovna-skupina-za-spremljanje-izvajanja-zdr-1/
- GOV.SI FAQ DOCX files for service of termination, annual leave and holiday allowance, fixed-term employment, winter allowance, and REK-O collective-agreement reporting.
- OPSI evidence of collective agreements: https://podatki.gov.si/dataset/evidenca-kolektivnih-pogodb?resource_id=5e1048b0-1c94-4848-9be0-4666c4e134d0
- eUprava, SPOT, ESS, IRSD, and GOV.SI minimum-wage pages listed in the source manifest.

## Prompt Optimization

Added `strict_legal_rag_sl_v3` to `evaluation/optimizations/config.json` and exported it to Open WebUI/Ollama preset files.

The prompt enforces:

- Slovenian-only answers;
- Slovenian employment-law scope check;
- use only retrieved context;
- source priority: PISRS first, official government interpretations second, case law third;
- refusal for unsupported or out-of-domain questions;
- no foreign-law mixing or general-knowledge guessing.
- explicit citation on every supported non-refusal answer;
- stricter handling of short ambiguous questions;
- exact handling of thresholds, periods, and tiered legal calculations.

This is currently the highest-value optimization because the model can be changed later while retaining the same retrieval and refusal behavior.

## Model Choice

Hugging Face search found these relevant GaMS models:

- `cjvt/GaMS-1B-Chat`: Slovenian chat model, about 1.54B parameters, Apache-2.0, CPU-friendly candidate.
- `cjvt/GaMS-9B`: stronger Slovenian/Balkan-language candidate based on Gemma 2 9B, likely too heavy for this CPU-limited setup.

Recommendation:

1. Use `cjvt/GaMS-1B-Chat` as the preferred GaMS answer generator once served through Open WebUI or a compatible local endpoint.
2. Use `ul-fri-nlp-course-project-optimized:latest` as the current best runnable model on the remote Ollama endpoint; keep `mistral:7b`, `llama3:latest`, and `gemma3:4b` as comparison/fallback models.
3. Do not fine-tune now. Spend effort on official-source ingestion, chunking, metadata, citation checks, and refusal tests.

Live endpoint status on 2026-05-21:

- remote Ollama/Open WebUI through `.env` aliases is reachable;
- `ul-fri-nlp-course-project-optimized:latest`, `mistral:7b`, `llama3:latest`, and `gemma3:4b` are runnable evaluation candidates;
- `qwen2.5-coder:7b` is available but disabled in the default arena because it was too slow for routine smoke runs;
- `cjvt/GaMS-1B-Chat` remains the preferred Slovenian candidate, but it was not present in the discovered Ollama/Open WebUI model list.

## Evaluation Criteria

### Retrieval Metrics

Answerable hit rate:

- measured over factual and ambiguous answerable questions;
- a retrieval is a hit when the fraction of reference content terms found in the retrieved context is at least `0.35`;
- higher is better.

Unanswerable false evidence rate:

- measured over out-of-domain questions;
- a false evidence hit occurs when retrieved context overlaps enough with the reference refusal terms to look spuriously relevant;
- lower is better.

Average context length:

- number of context words retrieved per question;
- lower is better only if correctness is preserved, because short context reduces distraction and CPU inference cost.

Source-priority accuracy:

- manual/planned metric;
- answer is correct only if primary-law questions retrieve PISRS before case law or guidance;
- measured as the fraction of top-1/top-3 contexts whose `source_type` matches expected priority.

Freshness:

- implemented at source level through `official_source_monitor.json`, planned at per-answer citation level;
- each answer should cite a monitored source whose current status is reachable and, for PISRS register matches, `Veljaven predpis`;
- measured from `official_source_monitor.json`.

### Answer Metrics

Correctness, grounding, completeness, clarity:

- scored `0-5` by `evaluation/judge_eval.py`;
- historical live runs used LLM-as-a-judge with remote `llama3:latest`, a common evaluation pattern for RAG systems;
- the current compliance pass also reports the deterministic offline fallback, which is less semantically rich but repeatable without model-server availability.

Hallucination:

- scored `0-5`, where `0` means no hallucination;
- strict refusal should reduce this fastest.

Refusal accuracy:

- measured only on unanswerable questions;
- correct if the model refuses instead of answering.

Citation precision:

- planned manual/LLM-assisted metric;
- cited source is counted correct only if it directly supports the claim.

Article exactness:

- planned metric for statute questions;
- exact if the answer cites the expected article or a legally equivalent provision.

Temporal correctness:

- planned metric for values that change, such as minimum wage;
- answer must state the effective date and cite an official current source.

## What Works Best So Far

Best current approach: strict RAG over curated, verified primary-law chunks, with deterministic generation and refusal-first prompting.

What does not work well yet: using the current 500-chunk COLESLAW extraction as the main corpus. It retrieves too much case law and an old sector-specific collective agreement, which weakens statutory question answering.

Historical answer and fine-tuning artifacts that were generated before the latest corpus corrections should be treated as stale unless they are regenerated in the current run. The final claims use the corrected questions, corrected curated chunks, normalized BM25 retrieval summaries, deployed Open WebUI wrapper smoke tests, offline diagnostic smoke tests, manual review, and official source monitor snapshot.

Regenerated deployed-wrapper result for the corrected curated corpus, judged by the deterministic offline judge: RAG improved correctness from `1.85` to `2.85`, improved grounding from `1.00` to `3.95`, and reached `1.00` refusal accuracy on unanswerable questions. Normalized BM25 retrieval reached `1.000` answerable Hit@3 and `0.000` false-evidence rate with `200.4` average context words.

Strict top-1 retrieval is weaker: `python evaluation/retrieval_eval.py --quiet --top-k 1 --output /tmp/retrieval_top1.jsonl` reports answerable Hit@1 `0.938`. In the current repository state the failing top-1 item is `q015` ("Ali me lahko odpustijo?"), while `q011` ("Kakšne so omejitve nadurnega dela?") retrieves `ZDR-1, čl. 143` at rank 1. The final report therefore uses `Hit@3` explicitly rather than an ambiguous "hit rate" label.

Manual final Open WebUI spot-check: `evaluation/manual_eval_appendix.md` reviews all 20 answers from `ul-fri-slovenian-employment-law-rag-openwebui`. It found `17/20` correct or appropriately refused answers, `10/12` correct factual answers, `7/11` fully supported citations among non-refusal factual answers, `4/4` correct out-of-domain refusals, and `3/4` correct ambiguous-question refusals. The three substantive failures are `q009` (retrieves Article 55 but incorrectly refuses the fixed-term-contract question), `q012` (retrieves Article 137 but reverses who pays after the first 20 working days), and `q014` (starts with a useful ambiguity refusal but drifts into irrelevant notice-period text).

Offline prompt-smoke result for `strict_legal_rag_sl_v3` over the current curated corpus: RAG improved fallback correctness from `0.70` to `3.15`, improved grounding from `0.20` to `3.75`, reduced hallucination from `4.20` to `0.85`, and reached `1.00` refusal accuracy on unanswerable questions. This validates the refusal and citation prompt direction, but the manual failures confirm that generation faithfulness still needs either stronger model selection or a more extractive answer layer.

Partial live model comparison with the same v3 prompt and retrieved context found:

- `ul-fri-nlp-course-project-optimized:latest` handled `q003` and ambiguous `q013` better than the older wrapper, but still failed `q009` by over-refusing and failed `q012` by reversing the payer.
- `mistral:7b` answered `q003` correctly and gave a fuller `q013` notice-period answer, but also failed `q009` through over-refusal and failed `q012`.
- The interrupted comparison did not complete reliable measurements for `llama3:latest`, `gemma3:12b`, or the Qwen models, so they are not used for final claims.

## Final Open WebUI Deployment

The finalized Open WebUI picker option is `ul-fri-slovenian-employment-law-rag-openwebui`, displayed as "UL FRI Slovenian Employment Law RAG".
It uses:

- base chat model: `ul-fri-nlp-course-project-optimized:latest`;
- selected prompt: `strict_legal_rag_sl_v3`;
- deterministic settings: temperature `0.0`, top-p `1.0`, max output `500`, context window `4096`;
- public read access in Open WebUI;
- strict refusal for unsupported, out-of-domain, or context-free questions.

The companion Ollama model `ul-fri-slovenian-employment-law-rag:latest` was also created from the same prompt/settings.
Open WebUI's live chat registry did not immediately expose that newly created Ollama tag through `/api/models`, so the Open WebUI wrapper intentionally points at the already verified base model and stores the optimized system prompt/settings at the Open WebUI model level.
Smoke evidence is stored in `evaluation/results/openwebui_final_model_smoke.json` and records `strict_legal_rag_sl_v3`.

Next highest-impact RAG work:

1. Build a primary-law chunk corpus from the tracked PISRS sources with metadata: law, article, validity status, source URL, NPB version.
2. Add official GOV.SI/IRSD/MDDSZ explanatory pages as a separate lower-priority index.
3. Keep COLESLAW/sodnapraksa as a tertiary case-law demo index.
4. Add retrieval reranking that prefers `primary_law > official_interpretation > case_law`.
5. Expand the evaluation set with current-law questions and explicit out-of-scope refusal cases.

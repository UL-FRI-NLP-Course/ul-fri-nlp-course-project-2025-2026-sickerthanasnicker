# Manual Evaluation Appendix

Date: 2026-05-22

This appendix records the final offline/manual review after expanding the official corpus. It is not a qualified legal review. Existing Open WebUI answer files in `evaluation/results/manual_openwebui_eval_*.jsonl` are retained as historical live-endpoint artifacts from the earlier 20-question setup.

## Current Offline Regression

The reproducible local path is:

```bash
python -m ul_fri_nlp.evaluation.retrieval_eval --quiet
python -m ul_fri_nlp.evaluation.run_eval --provider offline --quiet
python -m ul_fri_nlp.evaluation.judge_eval --provider offline --quiet
python -m ul_fri_nlp.evaluation.visualize_results
```

Current metrics over 40 questions:

- Hit@3: `1.000`.
- False evidence: `0.000`.
- Average context length: `448.6` words.
- RAG correctness: `2.95`.
- RAG grounding: `4.83`.
- RAG hallucination: `1.68`.
- Supported citation rate: `1.00`.
- Out-of-scope refusal accuracy: `1.00`.

## Known Failure Fixes

| ID | Status | Evidence |
| --- | --- | --- |
| `q009` fixed-term contracts | Fixed in offline path | Retrieves `ZDR-1, čl. 55` first and cites the two-year limit. |
| `q012` sick-pay payer | Fixed and updated to current law | Current ZDR-1/ZZZS sources state employer burden for the first 30 working days and compulsory health insurance from the 31st day. |
| `q014` ambiguous leave | Fixed in offline path | Starts with an ambiguity warning and cites `ZDR-1, čl. 159` and `ZDR-1, čl. 161`. |

## Scope Note

The assistant remains informational only. The evaluation checks retrieval, citation discipline, and refusal behavior, but it does not certify legal correctness for real cases.

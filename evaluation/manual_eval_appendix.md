# Manual Evaluation Appendix

Date: 2026-05-21

This appendix is a manual spot-check of all 20 evaluation questions against the
final Open WebUI model option `ul-fri-slovenian-employment-law-rag-openwebui`.
It complements the automated retrieval and LLM-judge metrics; it is not a
qualified legal review.

Raw model outputs are stored in
`evaluation/results/manual_openwebui_eval_answers.jsonl`. Manual labels are
stored in `evaluation/results/manual_openwebui_eval_judgements.jsonl`.

## Retrieval Metric Clarification

The current default command:

```bash
python evaluation/retrieval_eval.py --quiet
```

uses `top_k=3` and currently reports:

- answerable hit rate / Hit@3: `1.000`;
- unanswerable false-evidence rate: `0.000`;
- average context length: `200.4` words.

A stricter diagnostic run with `--top-k 1` reports answerable Hit@1 `0.938`.
In the current repository state, the Hit@1 failure is `q015` ("Ali me lahko
odpustijo?"), not `q011`. The `q011` overtime question retrieves `ZDR-1, čl.
143` at rank 1 in both top-1 and top-3 runs. The final report therefore uses
the explicit label `Hit@3` instead of the ambiguous phrase "hit rate".

## Manual Label Definitions

- Correctness: `correct` if the answer materially matches the reference and
  does not introduce a misleading legal conclusion; `incorrect` otherwise.
- Citation OK: `yes` only if the answer cites a source/article that directly
  supports the key claim; `no` if the citation is missing, incomplete, or only
  supports a side claim.
- Refusal OK: `yes` when an out-of-scope or insufficiently specified question
  is refused appropriately; `n/a` when refusal is not expected.

## Reviewed Answers

| ID | Question type | Correctness | Citation OK | Refusal OK | Manual note |
| --- | --- | --- | --- | --- | --- |
| `q001` | factual | correct | yes | n/a | Correct 20 working-day minimum with ZDR-1 Article 159 citation. |
| `q002` | factual | correct | yes | n/a | Correctly says the right to annual leave is acquired when employment is concluded. |
| `q003` | factual | correct | no | n/a | Correct 15-day notice period, but the answer omits an explicit article citation. |
| `q004` | factual | correct | yes | n/a | Correctly states that the worker may terminate without stating a reason and cites Article 94. |
| `q005` | factual | correct | no | n/a | Correctly lists business, incapacity and fault reasons, but omits the Article 89 citation. |
| `q006` | factual | correct | yes | n/a | Gives the severance tiers and Article 108 citation; wording is slightly compressed but materially correct. |
| `q007` | factual | correct | no | n/a | Correct court-demand remedy, but the answer omits the Article 17 citation. |
| `q008` | factual | correct | yes | n/a | Correct six-month maximum and Article 125 citation. |
| `q009` | factual | incorrect | no | no | The retrieved Article 55 context contains the two-year rule, but the model incorrectly refuses. |
| `q010` | factual | correct | yes | n/a | Correct 30-minute break rule with Article 154 citation. |
| `q011` | factual | correct | yes | n/a | Correct overtime limits and Article 143 citation. |
| `q012` | factual | incorrect | no | n/a | The context says health insurance bears longer absence after the first 20 working days; the model incorrectly says the employer pays after 20 days. |
| `q013` | ambiguous | correct | yes | yes | Correctly treats the question as ambiguous and points to worker/employer notice-period sources. |
| `q014` | ambiguous | incorrect | no | no | Starts with a refusal but then drifts into irrelevant notice-period text and unsupported assumptions. |
| `q015` | ambiguous | correct | n/a | yes | Correctly refuses a broad dismissal question as underspecified. |
| `q016` | ambiguous | correct | n/a | yes | Correctly refuses a broad wage question as underspecified. |
| `q017` | unanswerable | correct | n/a | yes | Correctly refuses VAT as outside Slovenian employment law. |
| `q018` | unanswerable | correct | n/a | yes | Correctly refuses inheritance as outside Slovenian employment law. |
| `q019` | unanswerable | correct | n/a | yes | Correctly refuses Austrian minimum wage as outside Slovenian employment law. |
| `q020` | unanswerable | correct | n/a | yes | Correctly refuses company formation as outside Slovenian employment law. |

## Summary

- Correct or appropriate refusal: `17/20`.
- Correct factual answers: `10/12`.
- Explicitly supported citations for non-refusal factual answers: `7/11`.
- Refusal behavior on reviewed out-of-domain questions: `4/4`.
- Refusal behavior on ambiguous in-domain questions: `3/4`.

Main follow-up: improve answer-time citation enforcement and generation
faithfulness. The remaining substantive failures are generation failures rather
than retrieval failures: `q009` retrieves Article 55 but refuses, `q012`
retrieves Article 137 but reverses the payer after the first 20 working days,
and `q014` starts with a useful ambiguity refusal but drifts into irrelevant
notice-period text.

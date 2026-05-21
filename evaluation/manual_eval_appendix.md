# Manual Evaluation Appendix

Date: 2026-05-21

This appendix is a small human spot-check of the final Open WebUI model option
`ul-fri-slovenian-employment-law-rag-openwebui`. It complements the automated
retrieval and LLM-judge metrics; it is not a qualified legal review.

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
- average context length: `189.9` words.

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
| `q001` | factual | correct | yes | n/a | Correctly gives 20 working days and cites ZDR-1; extra leave-detail text is more verbose than needed. |
| `q003` | factual | correct | yes | n/a | Correctly gives 15 days for less than one year and cites Article 94. |
| `q006` | factual | correct | yes | n/a | Correct tiered severance formula with ZDR-1 Article 108 citation. |
| `q011` | factual | correct | no | n/a | Overtime limits are correct, but the final answer omits the explicit ZDR-1 Article 143 citation. |
| `q012` | factual | incorrect | no | n/a | The question asks who pays after the first 20 working days; the answer repeats only that the employer pays the first 20 days. |
| `q015` | ambiguous | incorrect | no | no | The question is underspecified; the model should ask for context or refuse. It instead gives a broad answer and overstates the severance implication. |
| `q017` | unanswerable | correct | n/a | yes | Correctly refuses a VAT question as outside Slovenian employment law. |
| `q020` | unanswerable | correct | n/a | yes | Correctly refuses company-formation guidance as outside scope. |

## Summary

- Correct or appropriate refusal: `6/8`.
- Explicitly supported citations for non-refusal answers: `3/6`.
- Refusal behavior on reviewed out-of-domain questions: `2/2`.
- Refusal behavior on the reviewed ambiguous in-domain question: `0/1`.

Main follow-up: improve answer-time citation enforcement and ambiguity handling.
In particular, `q012` needs a context-aware answer about the payer after the
initial employer-funded period, and `q015` should not answer broadly without
facts about the employment status, reason for dismissal, protected status, and
procedure.

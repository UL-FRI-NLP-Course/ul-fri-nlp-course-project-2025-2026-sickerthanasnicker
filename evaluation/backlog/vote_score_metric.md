# Queued Plan: Vote Score Metric

Status: implemented in `evaluation/vote_eval.py`.

This plan is compatible with the optimization work and should consume existing answer files without rerunning answer generation.

## Goal

Add a separately runnable metric where each voter model sees a fresh shared context and anonymized candidate answers for the same question, including its own answer, then ranks the candidates.

## Proposed Script

Implemented as `evaluation/vote_eval.py`.

Inputs:

- `evaluation/questions.jsonl`
- an existing answers file, for example `evaluation/results/arena_answers.jsonl`
- optional retrieval chunks/top-k config for fresh shared context

Outputs:

- `evaluation/results/vote_eval.jsonl`
- `evaluation/results/vote_summary.csv`

## Voting Protocol

- Group answer rows by question id and variant, normally compare only `rag` rows.
- Exclude `raw_rag_prompt` by default.
- Exclude rows with model-call errors.
- Shuffle candidate answers deterministically per question.
- Replace model identities with labels such as `A`, `B`, `C`.
- Ask each configured voter model to rank the anonymized answers from best to worst.
- The voter prompt should emphasize correctness, grounding, refusal behavior for unanswerable questions, and hallucination penalties.

## Metrics

- `normalized_vote_score`: Borda-style score normalized to 0-1.
- `vote_score_mean`: average score from all voters.
- `vote_score_by_other_models`: average score excluding the candidate model's own vote.
- `self_vote_score`: score assigned by the same model to its own answer.
- `self_bias`: self vote minus other-model vote.
- `self_rank_delta`: own answer rank compared with average rank from other voters.

## Visualization

Implemented: `evaluation/visualize_results.py` accepts `--vote-summary` and adds charts for:

- vote score by model;
- self-bias by model;
- vote score vs judge correctness.

## Test Commands

Smoke test:

```bash
python evaluation/vote_eval.py \
  --answers evaluation/results/arena_smoke_answers.jsonl \
  --provider offline \
  --output evaluation/results/vote_eval_smoke.jsonl
```

Full existing-output run:

```bash
python evaluation/vote_eval.py \
  --answers evaluation/results/arena_answers.jsonl \
  --output evaluation/results/vote_eval.jsonl
```

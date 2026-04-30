# Fine-Tuning Data

This folder contains grounded QA examples prepared from the evaluation set.
It is intentionally a preparation step only: it does not run expensive PEFT,
LoRA, or Ollama model creation by default.

Each row uses chat-style JSONL:

- system: domain and grounding rules;
- user: retrieved context plus question;
- assistant: ideal grounded answer or refusal.

Possible next steps:

- use these rows as a tiny sanity dataset for LoRA/PEFT experiments;
- expand with more COLESLAW-derived employment-law QA pairs;
- create an Ollama Modelfile that bakes in the system prompt;
- evaluate any tuned model with `python evaluation/run_eval.py --arena`.

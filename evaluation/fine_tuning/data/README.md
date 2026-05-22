# Fine-Tuning Data

This folder contains grounded QA examples prepared from the evaluation set.
It is intentionally a preparation step only: it does not run expensive PEFT,
LoRA, or Ollama model creation by default.

For the final submission these files are marked exploratory and are not used
for the reported model choice. The project selected RAG-only optimization
because the target machine is CPU-limited and the lab recommendation was to
commit to one main approach. Some generated rows may reflect older retrieval
contexts from the COLESLAW-heavy sample; regenerate them before using them for
any future fine-tuning claim.

Each row uses chat-style JSONL:

- system: domain and grounding rules;
- user: retrieved context plus question;
- assistant: ideal grounded answer or refusal.

Possible future-only next steps:

- use these rows as a tiny sanity dataset for LoRA/PEFT experiments;
- expand with more COLESLAW-derived employment-law QA pairs;
- create an Ollama Modelfile that bakes in the system prompt;
- evaluate any tuned model with `python -m ul_fri_nlp.evaluation.run_eval --arena`.

# Slovenian Employment-Law RAG Assistant

Question-answering assistant for Slovenian employment law. Uses retrieval-augmented generation over official sources (PISRS, GOV.SI, MDDSZ, ZZZS, and related agencies), cites retrieved material, and refuses unsupported or out-of-scope questions.

Deployed at <https://ai.koderverse.com/>.

---

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make setup
make verify
```

`make verify` runs retrieval metrics, offline generation and judging, regenerates charts, and builds the report PDF into `report/.out/report.pdf`.

---

## Key Make Targets

| Target | What it does |
| --- | --- |
| `make setup` | Install dependencies and validate config |
| `make verify` | Full reproducibility check (retrieval + offline eval + report) |
| `make retrieval` | Retrieval metrics only (Hit@3, false evidence rate) |
| `make offline-eval` | Deterministic offline generation + judging + charts |
| `make corpus` | Rebuild official-source corpus from scratch |
| `make report` | Compile report PDF into `report/.out/` |
| `make source-monitor` | Check all 37 official source URLs are reachable |

---

## Configuration

For offline evaluation no configuration is needed.

For live model calls, copy the example and fill in your endpoints:

```bash
cp evaluation/config.example.env .env
```

Variables accepted:

- `OLLAMA_HOST` or `OLLAMA_URL`
- `WEBUI_HOST`, `OPENWEBUI_HOST`, or `OPENWEBUI_URL`
- `WEBUI_API_KEY` or `OPENWEBUI_API_KEY`
- `OPENAI_API_KEY` (optional, for OpenAI-compatible judging)

`.env` is gitignored. Never commit secrets.

---

## Corpus

The committed corpus is `report/code/data/chunk.jsonl` — 1,371 chunks:

- 1,059 PISRS primary-law chunks
- 189 official interpretation chunks
- 93 operational-guidance chunks
- 30 tertiary case-law chunks

Rebuild from official sources:

```bash
make corpus
```

---

## Deployment

### Ollama

```bash
# Set OLLAMA_URL in .env, then:
python -m optimizations.create_ollama_model --verify
ollama run ul-fri-slovenian-employment-law-rag
```

Evaluate:

```bash
python -m evaluation.run_eval \
  --provider ollama \
  --model ul-fri-slovenian-employment-law-rag:latest
```

### Open WebUI

Set `WEBUI_HOST` and `WEBUI_API_KEY` in `.env`, then register the preset:

```bash
python -m optimizations.create_ollama_model \
  --skip-create \
  --register-openwebui \
  --smoke-openwebui
```

The final deployed preset is `ul-fri-slovenian-employment-law-rag-openwebui` backed by the `strict_legal_rag_sl_v3` system prompt at temperature 0.

---

## System Requirements

- Python 3.10+
- TeX Live with `pdflatex` and `bibtex` (for report PDF)
- Network access only for corpus rebuild or source monitoring
- Optional: Ollama or Open WebUI for live generation

PEFT/fine-tuning dependencies are in `evaluation/optimizations/requirements-peft.txt` (not required for RAG pipeline).

---

## Compliance and Grade

See `compliance.md` for course requirement coverage and `grade.md` for the grading estimate.

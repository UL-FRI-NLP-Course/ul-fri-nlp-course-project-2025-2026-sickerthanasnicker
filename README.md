# AI Chat Assistant for the Law Domain

This project focuses on building an AI chat assistant for the Slovenian law domain. The main goal is to help users get quick and understandable answers to legal questions while keeping the responses grounded in official legal sources.

The planned system is centered around retrieval-augmented generation. Instead of relying only on the model's internal knowledge, the assistant should retrieve relevant passages from official Slovenian legal documents and generate answers based on those sources. This is intended to improve factual accuracy, reduce hallucinations, and make it easier to reference the legal basis behind each answer.

## Repository status

The repository now includes a working BM25 retrieval baseline. The system filters employment law documents, builds a search index, and returns relevant legal passages for a given query. LLM-based answer generation and full COLESLAW corpus integration are planned for the next submission.

## Project build instructions

Possible package requirements for the current repository contents:

* a TeX Live installation with `latexmk`
* LaTeX packages commonly bundled in `texlive-latexextra`, `texlive-pictures`, and `texlive-fontsrecommended`
* Visual Studio Code with the recommended LaTeX extension for the workspace

The compiled PDF is written to `report/.out/report.pdf`.

To run the retrieval system:

```
pip install rank-bm25
python src/rag.py
```

To build the index from the full COLESLAW corpus:

```
python src/rag.py --build <path_to_coleslaw>
```

## Repository structure

```
.
├── .vscode/
├── .gitignore
├── LICENSE
├── README.md
├── report/
└── src/
    ├── rag.py
    └── data/
        └── chunks.jsonl
```

* `report/`: project report and supporting LaTeX files
* `src/rag.py`: BM25 retrieval over employment law corpus
* `src/data/chunks.jsonl`: sample corpus chunks (ZDR-1)

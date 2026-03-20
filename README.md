# AI Chat Assistant for the Law Domain

This project focuses on building an AI chat assistant for the Slovenian law domain. The main goal is to help users get quick and understandable answers to legal questions while keeping the responses grounded in official legal sources.

The planned system is centered around retrieval-augmented generation. Instead of relying only on the model's internal knowledge, the assistant should retrieve relevant passages from official Slovenian legal documents and generate answers based on those sources. This is intended to improve factual accuracy, reduce hallucinations, and make it easier to reference the legal basis behind each answer.

## Repository status

At the moment, this repository mainly contains the project report and supporting LaTeX files. The implementation of the assistant, data-processing pipeline, and reproducible training or evaluation workflow will be documented here as they are added to the repository.

## Project build instructions

Possible package requirements for the current repository contents:

- a TeX Live installation with `latexmk`
- LaTeX packages commonly bundled in `texlive-latexextra`, `texlive-pictures`, and `texlive-fontsrecommended`
- Visual Studio Code with the recommended LaTeX extension for the workspace


The compiled PDF is written to `report/.out/report.pdf`.

## Repository structure

```text
.
├── .vscode/
├── .gitignore
├── LICENSE
├── README.md
└── report/
```

- `report/`: project report and supporting LaTeX files

# Ollama Model Export

This folder contains the generated Ollama Modelfile for the optimized Slovenian employment-law assistant.

Create or refresh the evaluated Ollama wrapper model:

```bash
python -m ul_fri_nlp.optimizations.create_ollama_model --verify
```

Run it:

```bash
ollama run ul-fri-slovenian-employment-law-rag
```

This model is an Ollama prompt/config model based on the best evaluated runnable base, `ul-fri-nlp-course-project-optimized:latest`. It uses the selected `strict_legal_rag_sl_v3` system prompt and deterministic generation settings.

Register or refresh the final Open WebUI picker option:

```bash
python -m ul_fri_nlp.optimizations.create_ollama_model --skip-create --register-openwebui --smoke-openwebui
```

The Open WebUI model id is `ul-fri-slovenian-employment-law-rag-openwebui`, displayed as "UL FRI Slovenian Employment Law RAG". The wrapper points at `ul-fri-nlp-course-project-optimized:latest`, because that base model is already present in Open WebUI's chat registry; the separate Ollama model `ul-fri-slovenian-employment-law-rag:latest` is also created for local Ollama use.

For real weight fine-tuning, use:

```bash
pip install -r evaluation/optimizations/requirements-peft.txt
python -m ul_fri_nlp.optimizations.train_lora
python -m ul_fri_nlp.optimizations.merge_lora
```

The PEFT path should be run on Colab/Kaggle or another suitable GPU environment. The local GTX 1080 / 8 GB setup is expected to be tight for Mistral 7B training.

After merging the adapter, import the merged checkpoint into Ollama with:

```bash
ollama create ul-fri-nlp-course-project-peft --experimental -f evaluation/optimizations/ollama/Modelfile.peft.example
```

# Ollama Model Export

This folder contains the generated Ollama Modelfile for the optimized Slovenian employment-law assistant.

Create or refresh the local Ollama model:

```bash
python evaluation/optimizations/create_ollama_model.py
```

Run it:

```bash
ollama run ul-fri-nlp-course-project-optimized
```

This model is an Ollama prompt/config model based on `mistral:7b`. It is immediately usable locally and uses the optimized system prompt plus a few grounded examples from the prepared training data.

For real weight fine-tuning, use:

```bash
pip install -r evaluation/optimizations/requirements-peft.txt
python evaluation/optimizations/train_lora.py
python evaluation/optimizations/merge_lora.py
```

The PEFT path should be run on Colab/Kaggle or another suitable GPU environment. The local GTX 1080 / 8 GB setup is expected to be tight for Mistral 7B training.

After merging the adapter, import the merged checkpoint into Ollama with:

```bash
ollama create ul-fri-nlp-course-project-peft --experimental -f evaluation/optimizations/ollama/Modelfile.peft.example
```

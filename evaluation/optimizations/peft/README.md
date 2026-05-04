# PEFT Runtime

This folder contains the GPU-capable container setup for the LoRA training path.

## Build

```bash
podman build -f evaluation/optimizations/peft/Containerfile -t ul-fri-nlp-peft .
```

## Run

Use the host repository as a bind mount so the container can see the prepared datasets and write outputs back into the workspace:

```bash
docker run --rm -it \
  --device nvidia.com/gpu=all \
  -v "$PWD:/workspace:Z" \
  -w /workspace \
  ul-fri-nlp-peft
```

The container starts through `run_peft` and checks that CUDA is visible before it begins training.

## Training Steps

Inside the container, run:

```bash
python evaluation/optimizations/prepare_peft_dataset.py
python evaluation/optimizations/train_lora.py
python evaluation/optimizations/merge_lora.py
```

Or let the container handle the whole sequence:

```bash
docker run --rm -it \
  --device nvidia.com/gpu=all \
  -v "$PWD:/workspace:Z" \
  -w /workspace \
  ul-fri-nlp-peft all
```

Then import the merged checkpoint into Ollama with:

```bash
ollama create ul-fri-nlp-course-project-peft --experimental -f evaluation/optimizations/ollama/Modelfile.peft.example
```

## What Can Run Now

These steps do not need the PEFT container and can run immediately on the current host:

```bash
python evaluation/optimizations/prepare_peft_dataset.py
python evaluation/optimizations/create_ollama_model.py
ollama run ul-fri-nlp-course-project-optimized
```

## GPU Linking

The most reliable path is to let Podman expose the NVIDIA GPU directly with `--device nvidia.com/gpu=all` and keep the Python stack inside the container. That avoids the host Python 3.14 mismatch while still using the system GPU drivers.
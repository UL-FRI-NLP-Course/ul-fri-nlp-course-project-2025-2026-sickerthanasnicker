#!/usr/bin/env bash
# Usage: ./evaluation/optimizations/peft/train.sh [model] [extra train_lora.py args...]
# Must be run from repo root.
set -euo pipefail

MODEL="${1:-microsoft/Phi-3.5-mini-instruct}"
shift 2>/dev/null || true

# Derive slug from model name: take last path component, lowercase, replace _ with -
MODEL_SLUG=$(echo "${MODEL##*/}" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
OUTPUT_DIR="evaluation/optimizations/peft_out/${MODEL_SLUG}-employment-law-lora"

HF_CACHE="$HOME/.cache/huggingface"
mkdir -p "$HF_CACHE"

echo "Model:      $MODEL"
echo "Output dir: $OUTPUT_DIR"
echo "HF cache:   $HF_CACHE"

exec docker run --rm \
  --device nvidia.com/gpu=all \
  --shm-size=16g \
  -e HF_HOME=/hf-cache \
  -e TRANSFORMERS_CACHE=/hf-cache \
  -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  -v "$HF_CACHE:/hf-cache" \
  -v "$PWD:/workspace:Z" \
  -w /workspace \
  --entrypoint python \
  ul-fri-nlp-peft:latest \
  evaluation/optimizations/train_lora.py \
    --model "$MODEL" \
    --output-dir "$OUTPUT_DIR" \
    --max-seq-length 512 \
    --epochs 3 \
    --batch-size 2 \
    "$@"

#!/usr/bin/env sh

set -eu

stage="${1:-all}"

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi
else
  echo "nvidia-smi is not available inside the container. GPU passthrough may not be configured." >&2
fi

python - <<'PY'
import sys

try:
    import torch
except Exception as exc:
    print(f"Failed to import torch: {exc}", file=sys.stderr)
    raise SystemExit(2)

if not torch.cuda.is_available():
    print("CUDA is not available inside the container. Start it with GPU passthrough before training.", file=sys.stderr)
    raise SystemExit(3)

print(f"CUDA ready: {torch.cuda.get_device_name(0)}")
PY

case "$stage" in
  prepare)
    python evaluation/optimizations/prepare_peft_dataset.py
    ;;
  train)
    python evaluation/optimizations/train_lora.py
    ;;
  merge)
    python evaluation/optimizations/merge_lora.py
    ;;
  all)
    python evaluation/optimizations/prepare_peft_dataset.py
    python evaluation/optimizations/train_lora.py
    python evaluation/optimizations/merge_lora.py
    ;;
  *)
    echo "Usage: run_peft [prepare|train|merge|all]" >&2
    exit 64
    ;;
esac
import argparse
import sys
from pathlib import Path


def require_training_stack():
    missing = []
    modules = {}
    for name in ("torch", "datasets", "transformers", "peft", "trl"):
        try:
            modules[name] = __import__(name)
        except Exception:
            missing.append(name)
    if missing:
        raise RuntimeError(
            "Missing PEFT training dependencies: "
            + ", ".join(missing)
            + ". Install them with: pip install -r evaluation/optimizations/requirements-peft.txt"
        )
    return modules


def get_format_fn(tokenizer):
    """Return a formatting function using the tokenizer's own chat template."""
    def format_fn(example):
        return tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
    return format_fn


# Legacy fallback (Mistral format) kept for scripts that import directly
def format_messages(example):
    lines = []
    for message in example["messages"]:
        role, content = message["role"], message["content"].strip()
        if role == "system":
            lines.append(f"<s>[INST] {content}\n")
        elif role == "user":
            lines.append(f"{content} [/INST]")
        elif role == "assistant":
            lines.append(f" {content}</s>")
    return "".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="Train a small LoRA adapter for the Slovenian employment-law assistant.")
    parser.add_argument("--model", default="TinyLlama/TinyLlama-1.1B-Chat-v1.0", help="Base model (default: TinyLlama 1.1B - fits on 8GB GPU). For GTX 1080: google/gemma-3-4b-it (needs HF_TOKEN) or TinyLlama.")
    parser.add_argument("--train", type=Path, default=Path("evaluation/optimizations/data/peft_train.jsonl"))
    parser.add_argument("--dev", type=Path, default=Path("evaluation/optimizations/data/peft_dev.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation/optimizations/peft_out/tinyllama-1.1b-employment-law-lora"))
    parser.add_argument("--offload-folder", type=Path, default=Path("/dev/shm/peft-offload"), help="RAM-backed offload folder to avoid NVMe writes")
    parser.add_argument("--max-seq-length", type=int, default=512, help="Reduced from 2048 for memory efficiency")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=1, help="Minimal for GPU memory: 1 example per step")
    parser.add_argument("--grad-accum", type=int, default=1, help="Minimal: no gradient accumulation")
    parser.add_argument("--learning-rate", type=float, default=5e-4, help="Higher LR for smaller model")
    parser.add_argument("--lora-r", type=int, default=8, help="Reduced from 16")
    parser.add_argument("--lora-alpha", type=int, default=16, help="Reduced from 32")
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--no-4bit", action="store_true", help="Disable 4-bit loading (use float16).")
    parser.add_argument("--cpu-only", action="store_true", help="Force CPU-only training (very slow).")
    parser.add_argument("--no-cpu-offload", action="store_true", help="Disable CPU offloading for GPU training.")
    parser.add_argument("--bf16", action="store_true", help="Use bfloat16 instead of float16 (requires GPU support).")
    return parser.parse_args()


def read_available_ram_gib():
    mem_available_kib = None
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as meminfo:
            for line in meminfo:
                if line.startswith("MemAvailable:"):
                    mem_available_kib = int(line.split()[1])
                    break
    except OSError:
        return None

    if mem_available_kib is None:
        return None
    return mem_available_kib / 1024 / 1024


def load_model_with_fallback(model_id, quantization_config, cpu_only, no_cpu_offload, offload_folder):
    """Load model with progressive fallback. Returns (model, device, is_quantized)."""
    import torch
    from transformers import AutoModelForCausalLM

    def _load(label, **kwargs):
        try:
            model = AutoModelForCausalLM.from_pretrained(model_id, low_cpu_mem_usage=True, trust_remote_code=True, **kwargs)
            print(f"✓ {label}", file=sys.stderr)
            return model
        except (ValueError, RuntimeError, TypeError, OSError) as exc:
            print(f"✗ {label} failed: {str(exc)[:150]}", file=sys.stderr)
            return None

    if cpu_only or not torch.cuda.is_available():
        reason = "CPU-only requested" if cpu_only else "no GPU"
        print(f"{reason}, loading float32 on CPU...", file=sys.stderr)
        model = _load("CPU float32", dtype=torch.float32)
        if model:
            return model, "cpu", False
        raise SystemExit(2)

    gpu_count = torch.cuda.device_count()
    gpu_budgets = {}
    gpu_budgets_with_cpu = {}
    cpu_gib = max(8, int((read_available_ram_gib() or 32) * 0.5))
    for i in range(gpu_count):
        free_bytes, total_bytes = torch.cuda.mem_get_info(i)
        free_gib = free_bytes / 1024**3
        # tight budget: leave 2.5 GiB headroom per GPU for activations/gradients
        tight = max(1, int(free_gib - 2.5))
        gpu_budgets[i] = f"{tight}GiB"
        gpu_budgets_with_cpu[i] = f"{tight}GiB"
        print(
            f"GPU {i}: {torch.cuda.get_device_name(i)} "
            f"({total_bytes/1e9:.1f}GB total, {free_gib:.1f}GB free, budget={tight}GiB)",
            file=sys.stderr,
        )
    gpu_budgets_with_cpu["cpu"] = f"{cpu_gib}GiB"

    offload_folder.mkdir(parents=True, exist_ok=True)

    # 1. 4-bit quantized, GPU-only (bitsandbytes cannot split quantized layers to CPU)
    if quantization_config is not None:
        model = _load(
            f"4-bit quantized across {gpu_count} GPU(s)",
            device_map="auto",
            max_memory=gpu_budgets,
            dtype=torch.float16,
            quantization_config=quantization_config,
        )
        if model:
            return model, "auto", True

    # 2. float16, GPU + CPU overflow (no quantization; accelerate handles offload transparently)
    model = _load(
        f"float16 across {gpu_count} GPU(s) + CPU overflow",
        device_map="auto",
        max_memory=gpu_budgets_with_cpu,
        dtype=torch.float16,
        offload_folder=str(offload_folder),
        offload_state_dict=True,
    )
    if model:
        return model, "auto-cpu", False

    # 3. float16, GPU-only (no CPU budget)
    model = _load(
        f"float16 across {gpu_count} GPU(s) only",
        device_map="auto",
        max_memory=gpu_budgets,
        dtype=torch.float16,
    )
    if model:
        return model, "auto", False

    # 4. CPU float32 (slow but guaranteed)
    print("All GPU strategies failed, loading float32 on CPU (slow)...", file=sys.stderr)
    model = _load("CPU float32", dtype=torch.float32)
    if model:
        return model, "cpu", False

    raise SystemExit(2)


def main():
    import os
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    args = parse_args()
    try:
        require_training_stack()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2

    import torch
    from datasets import load_dataset
    from peft import LoraConfig, prepare_model_for_kbit_training, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
    from trl import SFTTrainer

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    args.offload_folder.mkdir(parents=True, exist_ok=True)

    quantization_config = None
    if not args.no_4bit:
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            free_bytes, total_bytes = torch.cuda.mem_get_info(i)
            print(
                f"GPU {i} before load: {free_bytes / 1024**3:.2f} GiB free / {total_bytes / 1024**3:.2f} GiB total",
                file=sys.stderr,
            )
        torch.cuda.empty_cache()

    model, device_used, is_quantized = load_model_with_fallback(
        args.model,
        quantization_config,
        cpu_only=args.cpu_only,
        no_cpu_offload=args.no_cpu_offload,
        offload_folder=args.offload_folder,
    )

    if hasattr(model, "config"):
        model.config.use_cache = False

    if is_quantized:
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
        print("✓ Prepared for k-bit training", file=sys.stderr)

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    
    # Apply LoRA adapter to model for SFTTrainer
    model = get_peft_model(model, lora_config)
    print(f"✓ Applied LoRA: r={args.lora_r}, alpha={args.lora_alpha}", file=sys.stderr)

    dataset = load_dataset(
        "json",
        data_files={"train": str(args.train), "validation": str(args.dev)},
    )
    fmt = get_format_fn(tokenizer)
    dataset = dataset.map(lambda row: {"text": fmt(row)}, remove_columns=dataset["train"].column_names)

    model.config.pad_token_id = tokenizer.pad_token_id

    # fp16 AMP conflicts with models that have bf16 internal params (e.g. Phi-3.5).
    # For 4-bit QLoRA, bitsandbytes manages precision internally; no AMP needed.
    use_fp16 = device_used != "cpu" and torch.cuda.is_available() and not is_quantized
    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        logging_steps=5,
        save_strategy="epoch",
        eval_strategy="no",
        fp16=use_fp16,
        report_to=[],
        optim="adamw_torch",
        dataloader_pin_memory=False,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        args=training_args,
    )
    print("Starting training...", file=sys.stderr)
    trainer.train()
    print("Training complete, saving adapter...", file=sys.stderr)
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"✓ Saved LoRA adapter to {args.output_dir}")


if __name__ == "__main__":
    raise SystemExit(main())

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


def format_messages(example):
    lines = []
    for message in example["messages"]:
        role = message["role"]
        content = message["content"].strip()
        if role == "system":
            lines.append(f"<s>[INST] {content}\n")
        elif role == "user":
            lines.append(f"{content} [/INST]")
        elif role == "assistant":
            lines.append(f" {content}</s>")
    return "".join(lines)


def parse_args():
    parser = argparse.ArgumentParser(description="Train a small LoRA adapter for the Slovenian employment-law assistant.")
    parser.add_argument("--model", default="TinyLlama/TinyLlama-1.1B-Chat-v1.0", help="Base model (default: TinyLlama 1.1B - fits on 8GB GPU)")
    parser.add_argument("--train", type=Path, default=Path("evaluation/optimizations/data/peft_train.jsonl"))
    parser.add_argument("--dev", type=Path, default=Path("evaluation/optimizations/data/peft_dev.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation/optimizations/peft_out/tinyllama-1.1b-employment-law-lora"))
    parser.add_argument("--max-seq-length", type=int, default=512, help="Reduced from 2048 for memory efficiency")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--batch-size", type=int, default=2, help="Increased from 1 since TinyLlama is small")
    parser.add_argument("--grad-accum", type=int, default=4, help="Reduced from 8")
    parser.add_argument("--learning-rate", type=float, default=5e-4, help="Higher LR for smaller model")
    parser.add_argument("--lora-r", type=int, default=8, help="Reduced from 16")
    parser.add_argument("--lora-alpha", type=int, default=16, help="Reduced from 32")
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--no-4bit", action="store_true", help="Disable 4-bit loading (use float16).")
    parser.add_argument("--cpu-only", action="store_true", help="Force CPU-only training (very slow).")
    parser.add_argument("--no-cpu-offload", action="store_true", help="Disable CPU offloading for GPU training.")
    parser.add_argument("--bf16", action="store_true", help="Use bfloat16 instead of float16 (requires GPU support).")
    return parser.parse_args()


def load_model_with_fallback(model_id, quantization_config, cpu_only, no_cpu_offload):
    """Load model with simple GPU→CPU fallback. Works best with smaller models (1B-3B)."""
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig

    device_mapping_attempts = []
    
    if cpu_only:
        print("CPU-only mode requested.", file=sys.stderr)
        device_mapping_attempts = [(None, None, torch.float32)]
    elif torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)} ({torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB)", file=sys.stderr)
        # Try GPU with float16 (most memory-efficient)
        device_mapping_attempts.append(("cuda", None, torch.float16))
        # Fallback to CPU
        device_mapping_attempts.append((None, None, torch.float32))
    else:
        print("No GPU detected, using CPU.", file=sys.stderr)
        device_mapping_attempts = [(None, None, torch.float32)]

    last_error = None
    for device_map, quant_cfg, dtype in device_mapping_attempts:
        try:
            device_desc = device_map or "cpu"
            dtype_str = str(dtype).split('.')[-1].rstrip("'")
            print(f"Loading on {device_desc} with {dtype_str}...", file=sys.stderr)
            
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map=device_map,
                dtype=dtype,
                trust_remote_code=True,
            )
            print(f"✓ Loaded on {device_desc}", file=sys.stderr)
            return model, device_map or "cpu"
        except (ValueError, RuntimeError, TypeError, OSError) as exc:
            last_error = exc
            err_msg = str(exc)[:100]
            print(f"✗ Failed: {err_msg}", file=sys.stderr)
            continue

    print(f"Failed to load model: {last_error}", file=sys.stderr)
    raise SystemExit(2)


def main():
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

    # For TinyLlama and small models, quantization isn't needed
    quantization_config = None
    if args.no_4bit is False and "mistral" in args.model.lower():
        # Only use quantization for larger models like Mistral
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    model, device_used = load_model_with_fallback(
        args.model,
        quantization_config,
        cpu_only=args.cpu_only,
        no_cpu_offload=args.no_cpu_offload,
    )
    
    # Enable gradient checkpointing to reduce memory usage
    if hasattr(model, 'gradient_checkpointing'):
        model.gradient_checkpointing_enable()
        print("✓ Enabled gradient checkpointing", file=sys.stderr)
    
    if quantization_config is not None:
        model = prepare_model_for_kbit_training(model)
        print("✓ Prepared for 4-bit training", file=sys.stderr)

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
    dataset = dataset.map(lambda row: {"text": format_messages(row)}, remove_columns=dataset["train"].column_names)

    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        logging_steps=5,
        save_strategy="epoch",
        eval_strategy="epoch",
        fp16=True,
        report_to=[],
        optim="paged_adamw_8bit" if not args.no_4bit else "adamw_torch",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        args=training_args,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
    )
    print("Starting training...", file=sys.stderr)
    trainer.train()
    print("Training complete, saving adapter...", file=sys.stderr)
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"✓ Saved LoRA adapter to {args.output_dir}")


if __name__ == "__main__":
    raise SystemExit(main())

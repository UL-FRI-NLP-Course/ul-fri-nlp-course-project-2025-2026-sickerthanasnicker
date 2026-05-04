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
    parser.add_argument("--model", default="mistralai/Mistral-7B-Instruct-v0.3")
    parser.add_argument("--train", type=Path, default=Path("evaluation/optimizations/data/peft_train.jsonl"))
    parser.add_argument("--dev", type=Path, default=Path("evaluation/optimizations/data/peft_dev.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation/optimizations/peft_out/mistral-7b-employment-law-lora"))
    parser.add_argument("--max-seq-length", type=int, default=2048)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--no-4bit", action="store_true", help="Disable 4-bit loading.")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        require_training_stack()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2

    import torch
    from datasets import load_dataset
    from peft import LoraConfig, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainingArguments
    from trl import SFTTrainer

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization_config = None
    if not args.no_4bit:
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    if quantization_config is not None:
        model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )

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
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        peft_config=lora_config,
        args=training_args,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
    )
    trainer.train()
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"Saved LoRA adapter to {args.output_dir}")


if __name__ == "__main__":
    raise SystemExit(main())

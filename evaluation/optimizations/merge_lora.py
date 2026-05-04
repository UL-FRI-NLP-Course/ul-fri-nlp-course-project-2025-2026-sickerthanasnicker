import argparse
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Merge a PEFT LoRA adapter into a Hugging Face causal LM checkpoint.")
    parser.add_argument("--base-model", default="mistralai/Mistral-7B-Instruct-v0.3")
    parser.add_argument("--adapter", type=Path, default=Path("evaluation/optimizations/peft_out/mistral-7b-employment-law-lora"))
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation/optimizations/peft_out/mistral-7b-employment-law-merged"))
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:
        print(
            "Missing merge dependencies. Install with: "
            "pip install -r evaluation/optimizations/requirements-peft.txt",
            file=sys.stderr,
        )
        print(f"Import error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(model, args.adapter)
    merged = model.merge_and_unload()
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(args.output_dir, safe_serialization=True)
    tokenizer.save_pretrained(args.output_dir)
    print(f"Saved merged model to {args.output_dir}")
    print("To import a merged safetensors checkpoint into Ollama, use:")
    print(f"  ollama create ul-fri-nlp-course-project-peft --experimental -f <Modelfile using FROM {args.output_dir}>")


if __name__ == "__main__":
    raise SystemExit(main())

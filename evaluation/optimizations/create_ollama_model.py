import argparse
import subprocess
from pathlib import Path

from common import load_optimization_config, prompt_by_id, settings_by_id

from io_utils import load_jsonl


OLLAMA_DIR = Path(__file__).resolve().parent / "ollama"
DEFAULT_MODEL_NAME = "ul-fri-nlp-course-project-optimized"
DEFAULT_MODELFILE = OLLAMA_DIR / "Modelfile"
DEFAULT_EXAMPLES = Path("evaluation/optimizations/data/peft_train.jsonl")


def quote_block(text):
    return '"""' + text.replace('"""', '\\"\\"\\"').strip() + '"""'


def select_examples(path, count):
    examples = []
    if not path.exists() or count <= 0:
        return examples
    rows = load_jsonl(path)
    rows.sort(key=lambda row: row.get("metadata", {}).get("example_source") != "coleslaw_employment_chunk")
    for row in rows:
        messages = row.get("messages", [])
        if len(messages) != 3:
            continue
        user = messages[1]["content"]
        assistant = messages[2]["content"]
        source = row.get("metadata", {}).get("example_source", "")
        if source != "coleslaw_employment_chunk" and "ni mogoče" not in assistant.lower():
            continue
        if "ni mogoče" in assistant.lower() and len(examples) < max(1, count - 1):
            continue
        examples.append((user, assistant))
        if len(examples) >= count:
            break
    return examples


def build_modelfile(config, examples_path, example_count):
    export = config["webui_export"]
    prompt = prompt_by_id(config, export["prompt_id"])
    settings = settings_by_id(config, export["settings_id"])
    lines = [
        f"FROM {export['base_model_id']}",
        f"PARAMETER temperature {settings['temperature']}",
        f"PARAMETER top_p {settings['top_p']}",
        f"PARAMETER num_predict {settings['max_tokens']}",
        "PARAMETER num_ctx 4096",
        f"SYSTEM {quote_block(prompt['system'])}",
    ]
    for user, assistant in select_examples(examples_path, example_count):
        lines.append(f"MESSAGE user {quote_block(user)}")
        lines.append(f"MESSAGE assistant {quote_block(assistant)}")
    return "\n\n".join(lines) + "\n"


def parse_args():
    parser = argparse.ArgumentParser(description="Create the optimized Ollama model from the project prompt/config.")
    parser.add_argument("--config", type=Path, default=Path("evaluation/optimizations/config.json"))
    parser.add_argument("--examples", type=Path, default=DEFAULT_EXAMPLES)
    parser.add_argument("--example-count", type=int, default=3)
    parser.add_argument("--modelfile", type=Path, default=DEFAULT_MODELFILE)
    parser.add_argument("--model-name", default=DEFAULT_MODEL_NAME)
    parser.add_argument("--skip-create", action="store_true", help="Only write the Modelfile.")
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_optimization_config(args.config)
    args.modelfile.parent.mkdir(parents=True, exist_ok=True)
    args.modelfile.write_text(build_modelfile(config, args.examples, args.example_count), encoding="utf-8")
    print(f"Saved Ollama Modelfile to {args.modelfile}")
    if args.skip_create:
        return 0
    subprocess.run(["ollama", "create", args.model_name, "-f", str(args.modelfile)], check=True)
    print(f"Created Ollama model: {args.model_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

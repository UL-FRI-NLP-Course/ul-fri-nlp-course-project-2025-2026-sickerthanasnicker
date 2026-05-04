import argparse

from eval_config import load_env
from model_providers import list_ollama_models, list_openwebui_models


def parse_args():
    parser = argparse.ArgumentParser(description="List configured evaluation models.")
    parser.add_argument(
        "--provider",
        choices=["ollama", "openwebui", "all"],
        default="all",
        help="Model provider to query.",
    )
    return parser.parse_args()


def print_models(label, models):
    print(label)
    if not models:
        print("  (no models found)")
        return
    for model in models:
        print(f"  {model}")


def main():
    load_env()
    args = parse_args()

    if args.provider in ("ollama", "all"):
        try:
            print_models("Ollama models:", list_ollama_models())
        except Exception as exc:
            print(f"Ollama model lookup failed: {type(exc).__name__}: {exc}")

    if args.provider == "all":
        print()

    if args.provider in ("openwebui", "all"):
        try:
            print_models("Open WebUI models:", list_openwebui_models())
        except Exception as exc:
            print(f"Open WebUI model lookup failed: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()

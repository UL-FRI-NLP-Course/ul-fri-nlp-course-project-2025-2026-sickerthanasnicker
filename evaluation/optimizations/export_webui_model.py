import argparse
from pathlib import Path

from common import OPTIMIZATION_DIR, load_optimization_config, prompt_by_id, settings_by_id

from eval_config import load_env
from io_utils import write_json
from model_providers import _json_request, webui_headers, webui_host


DEFAULT_PRESET = OPTIMIZATION_DIR / "webui" / "optimized_model_preset.json"
DEFAULT_PAYLOAD = OPTIMIZATION_DIR / "webui" / "openwebui_create_model_payload.json"


def build_preset(config):
    export = config["webui_export"]
    prompt = prompt_by_id(config, export["prompt_id"])
    settings = settings_by_id(config, export["settings_id"])
    return {
        "id": export["model_id"],
        "name": export["name"],
        "base_model_id": export["base_model_id"],
        "description": "Optimized Slovenian employment-law RAG assistant preset.",
        "system_prompt": prompt["system"],
        "parameters": {
            "temperature": settings["temperature"],
            "top_p": settings["top_p"],
            "max_tokens": settings["max_tokens"],
            "seed": settings["seed"],
        },
        "metadata": {
            "project": "ul-fri-nlp-course-project",
            "prompt_id": prompt["prompt_id"],
            "prompt_label": prompt.get("label", prompt["prompt_id"]),
            "settings_id": settings["settings_id"],
            "training_status": "prompt_config_only_not_finetuned",
            "notes": (
                "Import this as a workspace/custom model in Open WebUI, or use the "
                "companion create payload if your Open WebUI version exposes the model creation API."
            ),
        },
    }


def build_openwebui_payload(preset):
    return {
        "id": preset["id"],
        "name": preset["name"],
        "base_model_id": preset["base_model_id"],
        "params": {
            "system": preset["system_prompt"],
            "temperature": preset["parameters"]["temperature"],
            "top_p": preset["parameters"]["top_p"],
            "seed": preset["parameters"]["seed"],
            "num_predict": preset["parameters"]["max_tokens"],
        },
        "meta": {
            "description": preset["description"],
            "tags": ["slovenian-law", "employment-law", "rag", "ul-fri-nlp"],
            "capabilities": {},
        },
    }


def parse_args():
    load_env()
    parser = argparse.ArgumentParser(description="Export an optimized Open WebUI model preset.")
    parser.add_argument("--config", type=Path, default=OPTIMIZATION_DIR / "config.json")
    parser.add_argument("--preset-output", type=Path, default=DEFAULT_PRESET)
    parser.add_argument("--payload-output", type=Path, default=DEFAULT_PAYLOAD)
    parser.add_argument(
        "--create",
        action="store_true",
        help="POST the generated payload to Open WebUI. Off by default to avoid mutating WebUI settings.",
    )
    parser.add_argument("--create-endpoint", default="/api/v1/models/create")
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_optimization_config(args.config)
    preset = build_preset(config)
    payload = build_openwebui_payload(preset)
    write_json(args.preset_output, preset)
    write_json(args.payload_output, payload)
    print(f"Saved preset: {args.preset_output}")
    print(f"Saved create payload: {args.payload_output}")

    if args.create:
        host = webui_host()
        if not host:
            raise RuntimeError("WEBUI_HOST is not configured.")
        url = f"{host}{args.create_endpoint}"
        response = _json_request(url, payload=payload, headers=webui_headers(), timeout=60)
        print(f"Open WebUI create response: {response}")


if __name__ == "__main__":
    main()

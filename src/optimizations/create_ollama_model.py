import argparse
import os
import subprocess
import urllib.error
from pathlib import Path

from evaluation.eval_config import load_env
from evaluation.io_utils import load_jsonl
from evaluation.model_providers import (
    _json_request,
    chat_openwebui,
    list_ollama_models,
    list_openwebui_models,
    ollama_host,
    webui_headers,
    webui_host,
)
from optimizations.common import (
    OPTIMIZATION_DIR,
    load_optimization_config,
    prompt_by_id,
    settings_by_id,
)


OLLAMA_DIR = OPTIMIZATION_DIR / "ollama"
DEFAULT_MODEL_NAME = "ul-fri-slovenian-employment-law-rag"
DEFAULT_MODELFILE = OLLAMA_DIR / "Modelfile"
DEFAULT_EXAMPLES = OPTIMIZATION_DIR / "data" / "peft_train.jsonl"


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


def build_modelfile(config, examples_path, example_count, base_model=None, prompt_id=None, settings_id=None):
    export = config["webui_export"]
    prompt = prompt_by_id(config, prompt_id or export["prompt_id"])
    settings = settings_by_id(config, settings_id or export["settings_id"])
    lines = [
        f"FROM {base_model or export['base_model_id']}",
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


def openwebui_payload(config, model_id, base_model_id):
    export = config["webui_export"]
    prompt = prompt_by_id(config, export["prompt_id"])
    settings = settings_by_id(config, export["settings_id"])
    return {
        "id": model_id,
        "base_model_id": base_model_id,
        "name": export.get("name", model_id),
        "params": {
            "system": prompt["system"],
            "temperature": settings["temperature"],
            "top_p": settings["top_p"],
            "num_predict": settings["max_tokens"],
            "num_ctx": 4096,
        },
        "meta": {
            "profile_image_url": "/static/favicon.png",
            "description": (
                "Final evaluated RAG-only Slovenian employment-law assistant. "
                "Use with Open WebUI document/RAG context; refuses unsupported "
                "or out-of-domain questions."
            ),
            "capabilities": {"vision": False, "citations": True},
            "tags": [
                "slovenian-employment-law",
                "rag",
                "pisrs",
                "official-sources",
            ],
        },
        "access_grants": [
            {
                "principal_type": "user",
                "principal_id": "*",
                "permission": "read",
            }
        ],
        "is_active": True,
    }


def register_openwebui_model(config, model_id, base_model_id):
    host = webui_host()
    if not host:
        raise RuntimeError("WEBUI_HOST/OPENWEBUI_URL is not configured.")
    payload = openwebui_payload(config, model_id, base_model_id)
    headers = webui_headers()
    try:
        row = _json_request(f"{host}/api/v1/models/create", payload=payload, headers=headers, timeout=30)
        action = "created"
    except urllib.error.HTTPError:
        row = _json_request(f"{host}/api/v1/models/model/update", payload=payload, headers=headers, timeout=30)
        action = "updated"
    _json_request(
        f"{host}/api/v1/models/model/access/update",
        payload={
            "id": model_id,
            "name": payload["name"],
            "access_grants": payload["access_grants"],
        },
        headers=headers,
        timeout=30,
    )
    return action, row


def smoke_openwebui_model(model_id):
    messages = [
        {
            "role": "user",
            "content": (
                "Kontekst:\n"
                "[1] Vir: ZDR-1, čl. 159; Letni dopust v posameznem koledarskem "
                "letu ne sme biti krajši kot štiri tedne. Za delavca, ki dela "
                "pet dni na teden, to pomeni najmanj 20 delovnih dni.\n\n"
                "Vprašanje: Koliko znaša minimalni letni dopust za delavca, "
                "ki dela pet dni na teden?"
            ),
        }
    ]
    options = {"temperature": 0.0, "top_p": 1.0, "max_tokens": 300, "seed": 42}
    return chat_openwebui(model_id, messages, options)


def parse_args():
    parser = argparse.ArgumentParser(description="Create the optimized Ollama model from the project prompt/config.")
    parser.add_argument("--config", type=Path, default=OPTIMIZATION_DIR / "config.json")
    parser.add_argument("--examples", type=Path, default=DEFAULT_EXAMPLES)
    parser.add_argument("--example-count", type=int, default=0)
    parser.add_argument("--modelfile", type=Path, default=DEFAULT_MODELFILE)
    parser.add_argument("--model-name", default=None)
    parser.add_argument("--base-model", default=None)
    parser.add_argument("--prompt-id", default=None)
    parser.add_argument("--settings-id", default=None)
    parser.add_argument("--skip-create", action="store_true", help="Only write the Modelfile.")
    parser.add_argument("--verify", action="store_true", help="Verify the created model appears in Ollama/Open WebUI model lists.")
    parser.add_argument("--register-openwebui", action="store_true", help="Create or update the final Open WebUI model wrapper.")
    parser.add_argument("--openwebui-model-id", default=None)
    parser.add_argument("--openwebui-base-model", default=None)
    parser.add_argument("--smoke-openwebui", action="store_true", help="Run a short Open WebUI chat smoke test after registration.")
    return parser.parse_args()


def main():
    load_env()
    args = parse_args()
    config = load_optimization_config(args.config)
    export = config["webui_export"]
    model_name = args.model_name or export.get("model_id") or DEFAULT_MODEL_NAME
    openwebui_model_id = args.openwebui_model_id or f"{export.get('model_id', model_name)}-openwebui"
    openwebui_base_model = args.openwebui_base_model or export.get("base_model_id")
    args.modelfile.parent.mkdir(parents=True, exist_ok=True)
    args.modelfile.write_text(
        build_modelfile(
            config,
            args.examples,
            args.example_count,
            base_model=args.base_model,
            prompt_id=args.prompt_id,
            settings_id=args.settings_id,
        ),
        encoding="utf-8",
    )
    print(f"Saved Ollama Modelfile to {args.modelfile}")
    if args.skip_create:
        if args.register_openwebui:
            action, _ = register_openwebui_model(config, openwebui_model_id, openwebui_base_model)
            print(f"Open WebUI model {action}: {openwebui_model_id}")
            if args.smoke_openwebui:
                print(smoke_openwebui_model(openwebui_model_id))
        return 0
    env = os.environ.copy()
    env["OLLAMA_HOST"] = ollama_host()
    subprocess.run(["ollama", "create", model_name, "-f", str(args.modelfile)], check=True, env=env)
    print(f"Created Ollama model: {model_name}")
    if args.verify:
        ollama_model_name = model_name if ":" in model_name else f"{model_name}:latest"
        ollama_models = set(list_ollama_models())
        print(f"Ollama verification: {'found' if ollama_model_name in ollama_models else 'missing'} {ollama_model_name}")
        try:
            webui_models = set(list_openwebui_models())
            print(f"Open WebUI verification: {'found' if ollama_model_name in webui_models else 'missing'} {ollama_model_name}")
        except Exception as exc:
            print(f"Open WebUI verification failed: {type(exc).__name__}: {exc}")
    if args.register_openwebui:
        action, _ = register_openwebui_model(config, openwebui_model_id, openwebui_base_model)
        print(f"Open WebUI model {action}: {openwebui_model_id}")
        webui_models = set(list_openwebui_models())
        print(f"Open WebUI wrapper verification: {'found' if openwebui_model_id in webui_models else 'missing'} {openwebui_model_id}")
        if args.smoke_openwebui:
            print(smoke_openwebui_model(openwebui_model_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

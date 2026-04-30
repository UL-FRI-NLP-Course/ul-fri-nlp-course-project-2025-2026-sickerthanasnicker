import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIR = Path(__file__).resolve().parent
CONFIG_FILE = EVALUATION_DIR / "config.json"
ROOT_ENV_FILE = PROJECT_ROOT / ".env"

DEFAULT_CONFIG = {
    "defaults": {
        "provider": "ollama",
        "model": "llama3:latest",
        "judge_provider": "ollama",
        "judge_model": "llama3:latest",
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 700,
        "seed": 42,
        "top_k": 3,
    },
    "arena_models": [
        {
            "model_id": "ollama-llama3",
            "provider": "ollama",
            "model": "llama3:latest",
            "enabled": True,
        },
        {
            "model_id": "ollama-mistral",
            "provider": "ollama",
            "model": "mistral:7b",
            "enabled": True,
        },
        {
            "model_id": "webui-project",
            "provider": "openwebui",
            "model": "ul-fri-nlp-course-project-eal",
            "enabled": True,
        },
    ],
}


def load_env(path=ROOT_ENV_FILE):
    """Load .env values without requiring python-dotenv."""
    try:
        from dotenv import load_dotenv

        load_dotenv(path, override=False)
        return
    except Exception:
        pass

    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_config(path=CONFIG_FILE):
    if not path.exists():
        return DEFAULT_CONFIG.copy()

    with open(path, encoding="utf-8") as fp:
        user_config = json.load(fp)

    config = DEFAULT_CONFIG.copy()
    config["defaults"] = {
        **DEFAULT_CONFIG["defaults"],
        **user_config.get("defaults", {}),
    }
    config["arena_models"] = user_config.get(
        "arena_models", DEFAULT_CONFIG["arena_models"]
    )
    return config


def env_or_config(env_name, config, key, default=None):
    value = os.environ.get(env_name)
    if value not in (None, ""):
        return value
    return config.get("defaults", {}).get(key, default)


def get_default_provider(config):
    return env_or_config("EVAL_PROVIDER", config, "provider", "ollama")


def get_default_model(config):
    return (
        os.environ.get("EVAL_MODEL")
        or os.environ.get("OLLAMA_MODEL")
        or config.get("defaults", {}).get("model", "llama3:latest")
    )


def get_default_judge_provider(config):
    return (
        os.environ.get("JUDGE_PROVIDER")
        or os.environ.get("EVAL_PROVIDER")
        or config.get("defaults", {}).get("judge_provider", "ollama")
    )


def get_default_judge_model(config):
    return (
        os.environ.get("JUDGE_MODEL")
        or os.environ.get("EVAL_MODEL")
        or os.environ.get("OLLAMA_MODEL")
        or config.get("defaults", {}).get("judge_model", "llama3:latest")
    )


def generation_options(config, args=None):
    defaults = config.get("defaults", {})
    values = {
        "temperature": defaults.get("temperature", 0.0),
        "top_p": defaults.get("top_p", 1.0),
        "max_tokens": defaults.get("max_tokens", 700),
        "seed": defaults.get("seed", 42),
    }

    if args is not None:
        for key in values:
            override = getattr(args, key, None)
            if override is not None:
                values[key] = override

    values["temperature"] = float(values["temperature"])
    values["top_p"] = float(values["top_p"])
    values["max_tokens"] = int(values["max_tokens"])
    values["seed"] = int(values["seed"])
    return values


def enabled_arena_models(config):
    return [model for model in config.get("arena_models", []) if model.get("enabled", True)]

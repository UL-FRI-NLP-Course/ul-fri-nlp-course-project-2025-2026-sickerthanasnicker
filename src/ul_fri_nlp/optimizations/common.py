import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVALUATION_DIR = PROJECT_ROOT / "evaluation"
OPTIMIZATION_DIR = EVALUATION_DIR / "optimizations"
CONFIG_FILE = OPTIMIZATION_DIR / "config.json"

from ul_fri_nlp.evaluation.io_utils import load_jsonl


def load_optimization_config(path=CONFIG_FILE):
    with open(path, encoding="utf-8") as fp:
        return json.load(fp)


def resolve_optimization_path(value):
    path = Path(value)
    if path.is_absolute():
        return path
    return OPTIMIZATION_DIR / path


def enabled_items(items):
    return [item for item in items if item.get("enabled", True)]


def find_by_id(items, key, value):
    for item in items:
        if item.get(key) == value:
            return item
    raise ValueError(f"No config item with {key}={value!r}.")


def select_items(items, key, selected_ids):
    active = enabled_items(items)
    if not selected_ids:
        return active
    selected = set(selected_ids)
    return [item for item in active if item.get(key) in selected]


def load_questions(path=None, limit=None):
    questions = load_jsonl(path or EVALUATION_DIR / "questions.jsonl")
    if limit is not None:
        return questions[:limit]
    return questions


def prompt_by_id(config, prompt_id):
    return find_by_id(config["prompts"], "prompt_id", prompt_id)


def settings_by_id(config, settings_id):
    return find_by_id(config["generation_settings"], "settings_id", settings_id)

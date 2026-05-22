import json
import os
import urllib.request


def _json_request(url, payload=None, headers=None, timeout=180):
    data = None
    method = "GET"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        method = "POST"

    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def ollama_host():
    return (
        os.environ.get("OLLAMA_HOST")
        or os.environ.get("OLLAMA_URL")
        or "http://localhost:11434"
    ).rstrip("/")


def webui_host():
    return (
        os.environ.get("WEBUI_HOST")
        or os.environ.get("OPENWEBUI_HOST")
        or os.environ.get("OPENWEBUI_URL")
        or ""
    ).rstrip("/")


def webui_headers():
    api_key = os.environ.get("WEBUI_API_KEY") or os.environ.get("OPENWEBUI_API_KEY") or ""
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def list_ollama_models():
    data = _json_request(f"{ollama_host()}/api/tags", timeout=30)
    return [item.get("name") for item in data.get("models", []) if item.get("name")]


def list_openwebui_models():
    host = webui_host()
    if not host:
        raise RuntimeError("WEBUI_HOST is not configured.")
    data = _json_request(f"{host}/api/models", headers=webui_headers(), timeout=30)
    models = data.get("data", data if isinstance(data, list) else [])
    result = []
    for item in models:
        if isinstance(item, dict):
            model_id = item.get("id") or item.get("name")
            if model_id:
                result.append(model_id)
        elif item:
            result.append(str(item))
    return result


def chat_ollama(model, messages, options):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": options["temperature"],
            "top_p": options["top_p"],
            "seed": options["seed"],
            "num_predict": options["max_tokens"],
        },
    }
    data = _json_request(f"{ollama_host()}/api/chat", payload=payload)
    return data.get("message", {}).get("content", "").strip()


def chat_openwebui(model, messages, options):
    host = webui_host()
    if not host:
        raise RuntimeError("WEBUI_HOST is not configured.")
    payload = {
        "model": model,
        "messages": messages,
        "temperature": options["temperature"],
        "top_p": options["top_p"],
        "max_tokens": options["max_tokens"],
        "seed": options["seed"],
        "stream": False,
    }
    data = _json_request(
        f"{host}/api/chat/completions",
        payload=payload,
        headers=webui_headers(),
    )
    choices = data.get("choices", [])
    if choices:
        message = choices[0].get("message", {})
        return message.get("content", "").strip()
    return data.get("response", "").strip()


def chat_openai(model, messages, options):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")
    payload = {
        "model": model,
        "messages": messages,
        "temperature": options["temperature"],
        "top_p": options["top_p"],
        "max_tokens": options["max_tokens"],
        "seed": options["seed"],
    }
    data = _json_request(
        "https://api.openai.com/v1/chat/completions",
        payload=payload,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    choices = data.get("choices", [])
    if not choices:
        return ""
    return choices[0].get("message", {}).get("content", "").strip()


def chat_model(provider, model, messages, options):
    if provider == "ollama":
        return chat_ollama(model, messages, options)
    if provider == "openwebui":
        return chat_openwebui(model, messages, options)
    if provider == "openai":
        return chat_openai(model, messages, options)
    raise ValueError(f"Unsupported provider: {provider}")

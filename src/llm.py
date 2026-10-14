"""Minimal Anthropic Messages API client (stdlib only). Returns None on any failure
so callers can fall back to deterministic logic."""
import json, os, urllib.request, urllib.error

API_URL = "https://api.anthropic.com/v1/messages"

def complete(prompt, system, model, max_tokens=120, timeout=30):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    body = json.dumps({
        "model": model, "max_tokens": max_tokens, "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(API_URL, data=body, method="POST", headers={
        "content-type": "application/json", "x-api-key": key,
        "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
        return "".join(b.get("text", "") for b in data.get("content", [])).strip()
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None

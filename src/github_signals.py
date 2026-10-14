"""Pull public GitHub signals for an organization (official REST API, no scraping).
Unauthenticated limit is 60 requests/hour; set GITHUB_TOKEN to raise it."""
import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cache")


def _days_since(iso):
    if not iso:
        return None
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).days


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_topics(repo):
    topics = repo.get("topics") or []
    if isinstance(topics, str):
        topics = [topics]
    return [str(t) for t in topics]


def _get(url):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "outbound-signal-pipeline"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
        return json.load(r)


def summarize(org, repos, keywords):
    """Pure function: turn a repo list into signals. Easy to unit test."""
    repo_list = repos or []
    active = [
        r for r in repo_list
        if _days_since(r.get("pushed_at")) is not None and _days_since(r.get("pushed_at")) <= 30
    ]
    top = max(repo_list, key=lambda r: _as_int(r.get("stargazers_count", 0))) if repo_list else None
    text = " ".join(
        f"{r.get('name','')} {(r.get('description') or '')} {' '.join(_safe_topics(r))}"
        for r in repo_list
    ).lower()
    hits = sorted({k for k in keywords if k in text})
    return {
        "org": org,
        "repo_count": len(repo_list),
        "total_stars": sum(_as_int(r.get("stargazers_count", 0)) for r in repo_list),
        "active_repos_30d": len(active),
        "days_since_last_push": min((_days_since(r.get("pushed_at")) for r in repo_list if r.get("pushed_at")), default=None),
        "top_repo": top.get("name") if top else None,
        "top_repo_stars": _as_int(top.get("stargazers_count", 0)) if top else 0,
        "selfhost_hits": hits,
        "error": None,
    }


def fetch_org_signals(org, keywords, fixture=None, use_cache=True):
    if fixture is not None:                       # offline / test mode
        return summarize(org, fixture.get(org, []), keywords)
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{org}.json")
    if use_cache and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                cached = json.load(fh)
            if isinstance(cached, list):
                return summarize(org, cached, keywords)
        except (OSError, ValueError, TypeError):
            pass
    try:
        repos = _get(f"https://api.github.com/orgs/{org}/repos?per_page=100&sort=pushed")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(repos, fh)
        return summarize(org, repos, keywords)
    except urllib.error.HTTPError as e:
        return {"org": org, "error": f"http_{e.code}"}
    except Exception as e:                          # network, JSON, etc.
        return {"org": org, "error": type(e).__name__}

"""Writes SYNTHETIC test data (fake orgs, fake repos) with dates relative to today.
Only for testing the code offline. Never use these as real prospects or real results."""
import json, os
from datetime import datetime, timedelta, timezone

def iso(days_ago):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")

FIXTURE = {
    "fake-selfhost-co": [
        {"name": "core", "description": "Self-host friendly platform with docker compose", "topics": ["docker"],
         "stargazers_count": 12000, "pushed_at": iso(2)},
        {"name": "helm-charts", "description": "Helm charts", "topics": ["kubernetes"],
         "stargazers_count": 400, "pushed_at": iso(5)},
        {"name": "sdk", "description": "SDK", "topics": [], "stargazers_count": 900, "pushed_at": iso(9)},
    ],
    "fake-quiet-co": [
        {"name": "old-lib", "description": "Legacy library", "topics": [], "stargazers_count": 80, "pushed_at": iso(400)},
    ],
    "fake-mid-co": [
        {"name": "api", "description": "API gateway", "topics": [], "stargazers_count": 2500, "pushed_at": iso(20)},
    ],
}

if __name__ == "__main__":
    path = os.path.join(os.path.dirname(__file__), "..", "data", "fixtures", "github_offline.json")
    json.dump(FIXTURE, open(path, "w"), indent=2)
    acc = os.path.join(os.path.dirname(__file__), "..", "data", "fixtures", "accounts_offline.csv")
    open(acc, "w").write("company,github_org,persona\nFake SelfHost Co,fake-selfhost-co,Platform Engineering Lead\n"
                         "Fake Quiet Co,fake-quiet-co,Head of Engineering\nFake Mid Co,fake-mid-co,VP Engineering\n"
                         "Fake Missing Co,not-in-fixture,CTO\n")
    print("fixtures written")

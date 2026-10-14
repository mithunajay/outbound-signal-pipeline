"""accounts.csv -> GitHub signals -> score -> personalized opener -> output/outreach_queue.csv
Usage: python src/run_pipeline.py [--offline] [--no-llm]"""
import argparse
import csv
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from github_signals import fetch_org_signals
from scoring import score_account
from personalize import personalize

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accounts", default=os.path.join(ROOT, "data", "accounts.csv"))
    ap.add_argument("--offline", action="store_true", help="use data/fixtures instead of GitHub API")
    ap.add_argument("--no-llm", action="store_true")
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(ROOT, "config.json")))
    fixture = json.load(open(os.path.join(ROOT, "data", "fixtures", "github_offline.json"))) if a.offline else None
    rows = list(csv.DictReader(open(a.accounts)))
    out, stats = [], {"total": len(rows), "enrich_ok": 0, "llm": 0, "fallback": 0}
    for r in rows:
        sig = fetch_org_signals(r["github_org"], cfg["icp"]["selfhost_keywords"], fixture)
        score, tier, reasons = score_account(sig, cfg)
        line, src = "", "skipped"
        if not sig.get("error"):
            stats["enrich_ok"] += 1
            if tier in ("A", "B"):
                line, src = personalize(sig, r["persona"], cfg, use_llm=not a.no_llm)
                stats["llm" if src == "llm" else "fallback"] += 1
        out.append({"company": r["company"], "github_org": r["github_org"], "persona": r["persona"],
                    "score": score, "tier": tier, "why": "; ".join(reasons),
                    "opener": line, "opener_source": src})
        if not a.offline:
            time.sleep(1)
    out.sort(key=lambda x: -x["score"])
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)
    path = os.path.join(ROOT, "output", "outreach_queue.csv")
    fieldnames = ["company", "github_org", "persona", "score", "tier", "why", "opener", "opener_source"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out)
    print(f"Wrote {path}")
    print(f"Enrichment success: {stats['enrich_ok']}/{stats['total']}")
    print(f"Openers: {stats['llm']} LLM-accepted, {stats['fallback']} template fallback")
    print("Tiers:", {t: sum(1 for o in out if o['tier'] == t) for t in 'ABC'})


if __name__ == "__main__":
    main()

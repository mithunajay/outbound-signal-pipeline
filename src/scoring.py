"""Transparent rule-based scoring so every score can be explained to Sales."""

def score_account(sig, cfg):
    if sig.get("error"):
        return 0, "C", [f"enrichment failed: {sig['error']}"]
    w, reasons, s = cfg["weights"], [], 0
    stars = sig["total_stars"]
    if stars >= 1000:
        s += w["stars_1k"]; reasons.append(f"{stars} total stars")
    if stars >= 10000:
        s += w["stars_10k"]; reasons.append("10k+ stars (large community)")
    a = sig["active_repos_30d"]
    if a >= 3:
        s += w["active_repos_3plus"]; reasons.append(f"{a} repos active in last 30d")
    elif a >= 1:
        s += w["active_repos_1plus"]; reasons.append(f"{a} repo active in last 30d")
    d = sig["days_since_last_push"]
    if d is not None and d <= 14:
        s += w["pushed_within_14d"]; reasons.append(f"last push {d}d ago")
    if sig["selfhost_hits"]:
        s += w["selfhost_signal"]; reasons.append("self-host signals: " + ", ".join(sig["selfhost_hits"]))
    if stars < cfg["icp"]["min_total_stars"]:
        s = min(s, 30); reasons.append("below ICP star threshold (capped)")
    tier = "A" if s >= cfg["tiers"]["A"] else "B" if s >= cfg["tiers"]["B"] else "C"
    return s, tier, reasons

"""LLM-written opener, with a guard. The model may only use facts we pass in.
If output is empty, too long, contains numbers we did not provide, or uses banned
phrases, we reject it and fall back to a deterministic template."""
import re
from llm import complete

BANNED = ["hope this email finds you", "i came across your", "quick question", "synergy", "game-changer"]
SYSTEM = ("You write one-sentence cold email openers for technical buyers. Use ONLY the facts "
          "given. Do not invent numbers, products, or claims. No flattery. Plain, specific, under "
          "{max_words} words. Output the sentence only.")

def template_line(sig):
    return (f"Noticed {sig['org']} has {sig['active_repos_30d']} repos with commits in the last 30 days, "
            f"led by {sig['top_repo']}.")

def validate(line, sig, max_words):
    if not line or len(line.split()) > max_words:
        return False, "length"
    if any(b in line.lower() for b in BANNED):
        return False, "banned_phrase"
    allowed = {str(sig.get(k)) for k in ("repo_count", "total_stars", "active_repos_30d",
               "days_since_last_push", "top_repo_stars")} | {"30"}
    for n in re.findall(r"\d[\d,]*", line):
        if n.replace(",", "") not in allowed:
            return False, "unsupported_number"
    low = line.lower()
    if sig["org"].lower() not in low and not (sig["top_repo"] and sig["top_repo"].lower() in low):
        return False, "no_grounding"
    return True, "ok"

def personalize(sig, persona, cfg, use_llm=True):
    mw = cfg["llm"]["max_words"]
    if use_llm:
        facts = (f"Company: {sig['org']}\nPersona: {persona}\nTop repo: {sig['top_repo']} "
                 f"({sig['top_repo_stars']} stars)\nRepos active last 30d: {sig['active_repos_30d']}\n"
                 f"Self-host signals: {', '.join(sig['selfhost_hits']) or 'none'}")
        raw = complete(facts, SYSTEM.format(max_words=mw), cfg["llm"]["model"], cfg["llm"]["max_tokens"])
        if raw is not None:
            clean = raw.strip().strip('"')
            ok, why = validate(clean, sig, mw)
            if ok:
                return clean, "llm"
            return template_line(sig), f"template(llm_rejected:{why})"
        return template_line(sig), "template(llm_unavailable)"
    return template_line(sig), "template(no_llm)"

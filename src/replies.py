"""Reply classification: LLM first (if key set), constrained to known labels,
keyword rules as fallback. Anything unclear goes to 'needs_human' rather than guessing."""
from llm import complete

LABELS = ["positive", "referral", "not_now", "negative", "auto_reply", "needs_human"]
SYSTEM = "Classify a reply to a cold email. Answer with exactly one label from: " + ", ".join(LABELS)

RULES = [
    ("auto_reply", ["out of office", "automatic reply", "auto-reply", "on leave"]),
    ("negative",   ["unsubscribe", "remove me", "not interested", "stop emailing", "spam"]),
    ("referral",   ["talk to", "reach out to", "forwarding", "cc'ing", "better person"]),
    ("not_now",    ["next quarter", "not now", "reach back", "bad timing"]),
    ("positive",   ["interested", "sounds good", "let's talk", "book", "demo", "send more", "call"]),
]

def keyword_label(text):
    t = text.lower()
    for label, kws in RULES:
        if any(k in t for k in kws):
            return label
    return "needs_human"

def classify(text, cfg, use_llm=True):
    if use_llm:
        out = complete(text, SYSTEM, cfg["llm"]["model"], 10)
        if out:
            out = out.strip().lower()
            if out in LABELS:
                return out, "llm"
    return keyword_label(text), "keyword"

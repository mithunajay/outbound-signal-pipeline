"""Compute outbound metrics from data/send_log.csv (you fill this from your sending tool).
Columns: company,sent,bounced,replied,reply_label,meeting_booked,cost_inr"""
import csv
import sys


def _b(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def _cost(v):
    if v in (None, ""):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().lower().replace("inr", "").replace("rs", "").replace("?", "").replace(",", "").replace(" ", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def compute(rows):
    sent = sum(_b(r.get("sent")) for r in rows)
    delivered = sent - sum(_b(r.get("bounced")) for r in rows)
    replies = [r for r in rows if _b(r.get("replied"))]
    positive = [r for r in replies if str(r.get("reply_label", "")).strip().lower() in ("positive", "referral")]
    meetings = sum(_b(r.get("meeting_booked")) for r in rows)
    cost = sum(_cost(r.get("cost_inr")) for r in rows)
    pct = lambda a, b: round(a / b * 100, 1) if b else None
    return {
        "accounts": len(rows), "sent": sent,
        "bounce_rate_pct": pct(sent - delivered, sent),
        "reply_rate_pct": pct(len(replies), delivered),
        "positive_reply_rate_pct": pct(len(positive), delivered),
        "meetings_booked": meetings,
        "cost_per_meeting_inr": round(cost / meetings, 2) if meetings else None,
        "total_cost_inr": round(cost, 2),
    }


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/send_log.csv"
    for k, v in compute(list(csv.DictReader(open(path)))).items():
        print(f"{k}: {v}")

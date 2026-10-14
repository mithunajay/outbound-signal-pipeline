import json, os, sys, unittest
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src")); sys.path.insert(0, os.path.dirname(__file__))
from make_fixture import FIXTURE
from github_signals import summarize
from scoring import score_account
from personalize import validate, template_line, personalize
from replies import keyword_label
from metrics import compute

CFG = json.load(open(os.path.join(ROOT, "config.json")))
KW = CFG["icp"]["selfhost_keywords"]

class T(unittest.TestCase):
    def test_strong_account_is_tier_a(self):
        sig = summarize("fake-selfhost-co", FIXTURE["fake-selfhost-co"], KW)
        s, tier, why = score_account(sig, CFG)
        self.assertEqual(tier, "A"); self.assertTrue(any("self-host" in w for w in why))

    def test_quiet_account_is_tier_c_and_capped(self):
        sig = summarize("fake-quiet-co", FIXTURE["fake-quiet-co"], KW)
        s, tier, _ = score_account(sig, CFG)
        self.assertEqual(tier, "C"); self.assertLessEqual(s, 30)

    def test_enrichment_failure_is_handled(self):
        s, tier, why = score_account({"org": "x", "error": "http_404"}, CFG)
        self.assertEqual((s, tier), (0, "C")); self.assertIn("failed", why[0])

    def test_guard_rejects_invented_numbers(self):
        sig = summarize("fake-selfhost-co", FIXTURE["fake-selfhost-co"], KW)
        ok, why = validate("fake-selfhost-co grew 300% this year", sig, 35)
        self.assertEqual((ok, why), (False, "unsupported_number"))

    def test_guard_rejects_banned_and_long(self):
        sig = summarize("fake-selfhost-co", FIXTURE["fake-selfhost-co"], KW)
        self.assertFalse(validate("I hope this email finds you well, fake-selfhost-co", sig, 35)[0])
        self.assertFalse(validate("word " * 50, sig, 35)[0])

    def test_template_passes_its_own_guard(self):
        sig = summarize("fake-selfhost-co", FIXTURE["fake-selfhost-co"], KW)
        self.assertTrue(validate(template_line(sig), sig, 35)[0])

    def test_no_llm_falls_back_to_template(self):
        sig = summarize("fake-selfhost-co", FIXTURE["fake-selfhost-co"], KW)
        line, src = personalize(sig, "CTO", CFG, use_llm=False)
        self.assertTrue(src.startswith("template"))

    def test_reply_keywords(self):
        self.assertEqual(keyword_label("Out of office until Monday"), "auto_reply")
        self.assertEqual(keyword_label("Please unsubscribe me"), "negative")
        self.assertEqual(keyword_label("Talk to our CTO, Priya"), "referral")
        self.assertEqual(keyword_label("Sounds good, can we book a call?"), "positive")
        self.assertEqual(keyword_label("Maybe next quarter"), "not_now")
        self.assertEqual(keyword_label("???"), "needs_human")

    def test_metrics(self):
        rows = [
            {"company": "a", "sent": "yes", "bounced": "no", "replied": "yes", "reply_label": "positive", "meeting_booked": "yes", "cost_inr": "100"},
            {"company": "b", "sent": "yes", "bounced": "yes", "replied": "no", "reply_label": "", "meeting_booked": "no", "cost_inr": "100"},
            {"company": "c", "sent": "yes", "bounced": "no", "replied": "no", "reply_label": "", "meeting_booked": "no", "cost_inr": "100"},
            {"company": "d", "sent": "yes", "bounced": "no", "replied": "yes", "reply_label": "negative", "meeting_booked": "no", "cost_inr": "100"},
        ]
        m = compute(rows)
        self.assertEqual(m["bounce_rate_pct"], 25.0)
        self.assertEqual(m["reply_rate_pct"], 66.7)   # 2 replies / 3 delivered
        self.assertEqual(m["positive_reply_rate_pct"], 33.3)
        self.assertEqual(m["cost_per_meeting_inr"], 400.0)

if __name__ == "__main__":
    unittest.main()

# Outbound Signal Pipeline

A small, real outbound-automation project: it turns public GitHub signals into a ranked
account list with a grounded, personalized opener, then measures what happens when you send.
Built to give you **real numbers and a real story** for GTM engineering applications.

**Important:** the files under `tests/` and `data/fixtures/` are SYNTHETIC test data. Never present
them as prospects or results. Only numbers you produce from your own real run count.

## What it does

```
accounts.csv -> GitHub signals -> score (explainable) -> LLM opener + guard -> outreach_queue.csv
                                                                    |
                         your sends -> send_log.csv -> metrics (reply rate, cost per meeting)
replies -> classifier (LLM, constrained labels, keyword fallback, "needs_human" when unsure)
```

Why it maps to a GTM Engineer job: trigger-based plays from product signals, enrichment with
error handling, LLM output that is validated instead of trusted, cost tracking, and metrics.

## Steps

### Phase 0 - Setup (30 min)
1. Install Python 3.10+. Unzip this project and open a terminal in the folder.
2. Run the tests: `python -m unittest discover -s tests -v` (all 9 should pass).
3. Try the demo on fake data: `python tests/make_fixture.py` then
   `python src/run_pipeline.py --offline --no-llm --accounts data/fixtures/accounts_offline.csv`
4. Optional keys (set as environment variables, never commit them):
   - `GITHUB_TOKEN` (raises the GitHub limit from 60 to 5000 requests/hour)
   - `ANTHROPIC_API_KEY` (enables LLM openers and reply classification; without it the code falls back to templates and keywords)

### Phase 1 - Pick a segment and build the seed list (1-2 days)
1. Choose ONE segment you can explain, e.g. "open-source developer tools with a self-hosted option".
2. Collect 50 real companies in it. Put each company's GitHub org in `data/accounts.csv`
   (columns: `company,github_org,persona`). Keep notes on where you found them.
3. Pick one buyer persona per company (e.g. Platform Engineering Lead).

### Phase 2 - Run the pipeline on real data (1 day)
1. `python src/run_pipeline.py` (add `--no-llm` if you have no key yet).
2. Open `output/outreach_queue.csv`. For each Tier A account read the `why` column and ask:
   does this ranking make sense to a human? Adjust `config.json` weights if not, and note what you changed and why.
3. Record: enrichment success rate, how many LLM openers were rejected by the guard (and why).
   A high rejection rate is a finding worth writing up, not something to hide.

### Phase 3 - Find contacts and track cost (1-2 days)
1. For Tier A/B accounts, find a real contact for the persona (Clay free tier, Apollo free tier, or LinkedIn by hand).
2. Verify the email before sending. Keep a simple cost log: credits or rupees spent per enriched record.
3. If a provider misses, try a second one and record the fallback hit rate. That is your "waterfall" evidence.

### Phase 4 - Send a SMALL real test (3-5 days)
1. Keep it to 20-30 sends. Use your own real identity and a short, honest message that uses the opener.
2. Include a clear way to opt out. Do not buy lookalike domains or send volume from a cold domain.
3. Send manually or with a sequencer you already have access to. Log each send.

### Phase 5 - Log results and classify replies (ongoing, 1 week)
1. Copy `data/send_log_template.csv` to `data/send_log.csv` and fill one row per send.
2. Classify replies: use `classify()` in `src/replies.py`, then review every `needs_human` and any
   LLM label you doubt. Fix the label in the log if the classifier was wrong, and count those errors.
3. Run `python src/metrics.py data/send_log.csv` for bounce rate, reply rate, positive reply rate,
   meetings booked, and cost per meeting.

### Phase 6 - Iterate once and write it up (1-2 days)
1. Compare Tier A vs Tier B reply rates. Change ONE thing (scoring weight, opener style, persona) and say why.
2. Write a one-page summary: segment, volume, what you sent, results with numbers, one change you made
   and what happened, what you would do next, and what failed. Failures make it credible.
3. Record a 3-5 minute Loom: the pipeline diagram, one Tier A account end to end, the guard rejecting a bad
   opener, and your metrics.

### Phase 7 - Update your resume
Replace the "design stage" line with a real one, using ONLY your real numbers:

> Built a signal-driven outbound pipeline (Python, GitHub API, Claude API): scored [N] open-source
> dev-tool accounts, sent [N] emails to [persona]; [X]% reply rate, [Y] meetings, Rs [Z] per meeting.
> Added an output guard that rejected [N]% of LLM openers; [one change you made and its effect].

If your results are small or zero meetings, say so plainly. "30 sends, 3 replies, 1 call" with a clear
lesson is far better than a claim that cannot survive a follow-up question.

## Files
- `config.json` - ICP threshold, scoring weights, tiers, model name
- `src/github_signals.py` - GitHub enrichment (cached, handles errors)
- `src/scoring.py` - explainable scoring
- `src/personalize.py` - LLM opener plus guard (length, banned phrases, unsupported numbers, grounding)
- `src/replies.py` - reply classifier with fallback and `needs_human`
- `src/metrics.py` - reply rate, bounce rate, cost per meeting
- `src/run_pipeline.py` - orchestrator
- `tests/` - 9 unit tests and a synthetic fixture generator

## Known limits (be upfront about these)
- Signals come from public GitHub activity only; it does not read Docker pulls or telemetry (Plane has those, you do not).
- Scoring is rule-based and untuned until you have real reply data.
- Model name in `config.json` may need updating to a model your key can access.

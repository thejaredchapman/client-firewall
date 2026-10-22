# Client Firewall

Keep one client's information out of another client's work in Claude.

A Claude Project template for anyone who works inside several companies at once. Before Claude drafts anything, it checks your message against that client's rules and answers 🟢 GREEN (go), 🟡 AMBER (clean up first) or 🔴 RED (another client's details, stop).

**Site with copy buttons and a demo to try:** https://client-firewall.vercel.app

## Set up in 3 steps

1. In claude.ai, create one Project per client.
2. Paste [`template/project-instructions.md`](template/project-instructions.md) into the Project's instructions.
3. Copy [`template/client-rules.template.md`](template/client-rules.template.md), fill it in for that client, name it `client-rules.md`, and add it to the Project's knowledge.

## Limits

- It only knows the clients you list in the rules file, plus obviously sensitive data.
- It's a second check, not a guarantee. The model can be wrong.
- You still decide what gets sent.

## Demo data

`demo/` holds three made-up clients and one made-up weekly notes doc. Every company, person and figure is invented.

## Measure the cost per check

In claude.ai the template runs on your plan with no per-call charge. `measure/measure_cost.py` recreates the same call through the API to show what it would cost.

```bash
python3 -m venv measure/.venv
measure/.venv/bin/pip install -r measure/requirements.txt
export ANTHROPIC_API_KEY=...   # never commit it
measure/.venv/bin/python measure/measure_cost.py --runs 3
measure/.venv/bin/python -m pytest tests
```

Prices live in `measure/prices.json` with the source URL and the date they were checked. Results go to `measure/results.csv` and `measure/summary.json`.

**Sample responses:** [`measure/sample-responses.md`](measure/sample-responses.md) shows one full reply from each model for each test message, with the exact system prompt and user message that produced it. Regenerate with `measure/.venv/bin/python measure/sample_responses.py`.

## Site and handout

```bash
cd site
npm install
npm run sync      # copy template/demo/summary files into site/content
npm test
npm run dev
npm run handout -- --url=https://client-firewall.vercel.app   # one-page PDF with QR code -> handout/
```

Made by Jared Chapman · linkedin.com/in/thejaredchapman · thejaredchapman.com

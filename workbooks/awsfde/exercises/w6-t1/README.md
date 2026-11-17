# awsfde/w6-t1 - Embedded dashboard blank on refresh, and one customer saw another customer's numbers

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 6 (Thu: GenerateEmbedUrl APIs, allowed domains and session lifecycle; Fri: the embedding backend)

## Symptom

The morning after web release 2026.11.05, four tickets arrive: Acme Foods and Delta Outfitters see a
blank dashboard on most page loads, Brightline Health gets logged out of analytics after about 15
minutes, and Corvid Logistics opened a P1: at 09:45 its ops lead saw Acme Foods' lanes and volumes in
Corvid's own portal. Nothing changed in Quick Sight: same dashboards, datasets and RLS rules. Read
`evidence/TICKETS.txt` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/TICKETS.txt`, `evidence/release-2026.11.05.md` | the tickets and what shipped |
| `evidence/page-loads.csv` | the morning's page loads (time, tenant, user, how long the browser took to redeem the URL) |
| `config/distribution.json` | the CloudFront distribution: behaviors and the cache policies they use (prod config) |
| `api/embed_handler.py` | the embed-URL Lambda behind `/api/analytics/embed-url` (prod code) |
| `edge/` | a CloudFront cache simulator driven by the distribution config, and a fake Quick Sight that issues single-use embed URLs valid for 5 minutes. Treat them as the environment, not the suspect. |
| `run/` | created by `make setup`: `cloudfront-access.log`, `lambda.log`, `quicksight-embed.log` (what each browser got when redeeming), `summary.json` |

## Your task

1. Find the root cause of the blank dashboards and of the cross-tenant view, with evidence from the
   edge logs, the Lambda log and the embed log. Explain exactly how Corvid saw Acme's data.
2. Decide which of the other findings (15-minute logout, the AllowedDomains wildcard) are related.
3. Fix it in `config/distribution.json` and `api/embed_handler.py` so the embed endpoint can never be
   served from a cache, as two independent layers, without losing what ASK-377 was for (catalog
   caching) or the static-asset caching.
4. Verify with `make test` and `make replay`.
5. Write `ANSWER.md`: root cause with evidence, the exposure statement for both customers, the fix
   and its verification, and how you would stop this class of change shipping again.

## Acceptance criteria (what the grader checks)

- The replay shows no blank dashboards, no cross-tenant views, and no edge hits on the embed endpoint.
- The Lambda sends `cache-control: no-store` on every response, and the edge would not cache the
  embed endpoint even if the origin forgot that header.
- Catalog API responses and static assets are still cached; tenant scoping in the Lambda is unchanged.
- `ANSWER.md` names the mechanism, quotes the evidence, separates the red herrings, and states the exposure.

## How to run

```bash
make setup     # replay into run/
make test
make replay    # after your fix
# from workbooks/: /grade awsfde/w6-t1
make clean
```

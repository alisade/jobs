# ANSWER: connect/w5-t1 The help desk bot quotes HR-only and retired articles

## Approach

Started from the retrieval log rather than the model: `jq -c '{caller,query,filteredCount,fallback}'
incident/retrieval-log.jsonl` shows every Finance/HR/Legal contact with filteredCount 0 and
fallback "unfiltered", while IT and anonymous wifi questions filter normally. The model only quoted
what retrieval gave it (invocation log: HR article as source [1]).

## Root cause

Trigger: exporter 2026.10.05 renamed the sidecar key department -> dept (`cat
incident/sidecars/KB0020456.html.metadata.json` shows "dept": "Finance"; diff line +dept). The
retriever filters department-restricted content with `equals department`; a filter on a key no
document has matches nothing (not an error), so restricted articles vanished for their own
departments. Latent defect: HD-2231 retries Retrieve with no filter when the filtered call returns
nothing, dropping audience, region and status - which served HR-only articles to Finance and the
retired RSA article KB0009001. Dashboard: filtered=0 rose from 2.1% (Sat) to 31% (Mon) when the
exporter ran at 02:00 on 2026-10-06. Blast radius from the replay: fin-uk/fin-us got KB0030001,
hr-us got KB0020457 and KB0040001, it-in got KB0030001/KB0020457, ctr-in got Finance and HR
articles, anonymous callers got IT articles including retired KB0009001.
Red herring: the 3 failed ingestion documents are attachments over the 10 KB metadata limit, the
same three on both days.

## Fix

Exporter writes exactly the schema attributes (department) and asserts them; retriever hands off
(NO_ARTICLES) instead of retrying unfiltered. make replay: 0 leaks, Finance/HR/Legal find their
articles, 0 unfiltered calls; make test green.

## Trade-offs / what I would do in production

Contract test shared by both pipelines (sidecar keys == schema == filter keys); alarm on filtered=0
rate by department; fail closed everywhere; consider Managed KB ServiceNow ACL crawl; InfoSec log
review and notification for the exposed HR/Legal articles.

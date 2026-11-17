# Reference: audit/w2-t1

Root cause: `fetch_closed_pulls` stops when `len(items) < per_page`. It asks for per_page=100; the
GHE appliance caps per_page at 50 (lowered in the upgrade), so the first page has 50 items, the
heuristic calls it the last page, and the loop ends after one request. The Link header on that
response says `...per_page=50&page=2>; rel="next"`. Only the 50 most recently updated closed PRs
were exported; 38 of them were merged to main in H1.

Evidence: `incident/export.log` DEBUG line for page 1 (per_page=100 requested, 50 items, rel="next"
present) and the INFO line "fetched 50 closed pulls ... in 1 request(s)". After the fix: 488 closed
pulls in 10 requests, population 421 = deploy log 421.

Red herrings: the time-zone filter is correct (boundary dates check out, and a TZ error moves a few
items at the period edges, not 383); token scope would produce 403/404, not 200s; the upgrade is
the trigger (it lowered the cap), not the defect.

Fix (`.grading/solution/popexport/client.py`): follow `rel="next"` until absent, bounded by
max_pages, with loop and duplicate detection. Also make the job fail when the population does not
reconcile to the control total, so a short extraction cannot be delivered silently.

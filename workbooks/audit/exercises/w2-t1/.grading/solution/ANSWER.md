# ANSWER: audit/w2-t1 The CM-03 population does not reconcile

## Approach

Read incident/export.log first: one request, 50 items, exit 0. That ruled out a filter problem
before looking at time zones: the PRs were never fetched.

## Root cause

`fetch_closed_pulls` treats a page shorter than per_page as the last page. It requests per_page=100;
the GHE appliance caps per_page at 50, so page 1 returns 50 < 100 and the loop stops. The response
carried `Link: <...per_page=50&page=2>; rel="next"`, which the client ignored. Log: "GET
...per_page=100&page=1 -> 200 (50 items) Link: ...rel="next"" and "fetched 50 closed pulls ... in 1
request(s)". Time zone: boundary conversions are correct and could only shift edge items. Token: every
call returned 200. The upgrade lowered the cap and exposed the bug; it is not the bug.

## Fix

The client follows rel="next" until absent, with a page limit, loop detection and a duplicate check.
After the fix, 488 closed pulls come back in 10 requests, and the population reconciles: 421 = 421.

## Trade-offs / what I would do in production

Note to the auditor: the H1 extraction was incomplete because of a client pagination defect. It has
been re-extracted (query, parameters and run log attached), and it reconciles to DeployHub's control
total. The job now fails when the population does not reconcile, and the reconciliation is part of
the workpaper.

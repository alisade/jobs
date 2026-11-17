# Volumes and targets

| Item | Value |
|---|---|
| Accounts | 410,000, growing 8% a year |
| Contacts | 2.3 M, growing 12% a year |
| Activities | 48 M today, 1.1 M new per month, peaks of 90 per second during the Q4 campaign window |
| Opportunities | 640,000, 9,000 stage changes per business day |
| Peak read traffic | 1,800 requests per second across all apps (support console is 60% of it) |
| Peak write traffic | 220 requests per second (activities dominate) |
| Agent traffic (forecast year 1) | 150 requests per second, bursty; each agent turn makes 3-8 tool calls |
| Account timeline | p95 < 200 ms for the newest 50 items on accounts with up to 400,000 activities |
| Support console reads | p95 < 150 ms |
| Retention | activities 7 years (legal hold possible), audit log 7 years, append-only |
| Average row sizes | account 2 KB, contact 1.5 KB, activity 1.2 KB, opportunity 3 KB (custom fields included) |
| RPO / RTO | 5 minutes / 1 hour for the platform database |

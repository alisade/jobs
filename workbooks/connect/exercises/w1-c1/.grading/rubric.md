# Rubric: connect/w1-c1 Harden the help desk inbound flow
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Failure handling design | 15 | Full: every Lambda/queue/transfer error leads somewhere a caller would accept (unverified-but-served, overflow, capacity message, technical-difficulties message); identification failure never blocks; no silent disconnects. Partial: lint-clean but some error branches route straight to Disconnect without a message. Zero: error branches wired to arbitrary actions just to satisfy lint. |
| 3 | Latency budgets | 10 | Full: identify <= 3 s with a stated reason (caller dead air, Connect retries within the 8 s sync limit, directory p99), reset <= 8 s, and ANSWER.md mentions async invoke (up to 60 s with Wait / Load Lambda result) or moving slow work out of the IVR. Partial: values right, no reasoning. |
| 4 | Routing correctness | 10 | Full: VIP and outage use UpdateContactRoutingBehavior QueuePriority 1, staffing check on the working queue, overflow sets a new working queue before transfer, retry loop is a Loop block with DoneLooping to GeneralSupport. Partial: correct but duplicated sub-graphs that should be a module. |
| 5 | Flow hygiene | 5 | Logging first, readable identifiers, no PII read back, no unreachable actions, prompts short and actionable. |
| 6 | ANSWER.md trade-offs | 10 | Full: at least three concrete production items with a position: flow modules for shared menus/messages, holiday and emergency-closure handling (hours overrides or a DynamoDB/Data Table check), callbacks vs overflow, prompt management and versions/aliases for release, CloudWatch alarms on ContactFlowErrors and flow logs retention. Partial: generic. |
Total: 100

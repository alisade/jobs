# PAGE: store associates report wrong stock answers (sev2, Black Friday)

**Opened:** 2026-11-28 18:20 PT by Store Ops  **Service:** kestrel-assistant (web + associate app)

> Store 087 (Fairview) associates: the assistant says the Glacier 45qt cooler is "in stock (6 left)".
> We have had zero since we opened. Three customers drove in for it. One associate says the answer
> even names a different store number. Store 012 says the same thing happened to them after lunch.

## Thread (#inc-assistant-stock)

**18:24 store-ops:** this is costing us customers on our biggest day. Can we turn the assistant off for
stock questions?

**18:27 inventory-oncall:** we had an inventory replication lag alert at 07:52 this morning
(`inventory-replica-lag > 60s` for 4 minutes, auto-resolved at 07:56). Maybe the assistant read stale
replicas? I checked the API just now and it returns 0 for KO-COOL-45 at 087.

**18:31 ai-team:** we shipped the answer cache on 11/20 for holiday load. FAQ hit rate is great.

**18:40 privacy (cc):** a customer at store 012 says the chat told them someone else's order was "out
for delivery". Please check whether that is related.

You are on call for the assistant. Find the root cause, fix it without losing the FAQ savings, and
tell privacy what happened.

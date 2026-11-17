# Design: shopping assistant service boundaries (three ADRs)

## Context and drivers

- **Fail soft.** INC-2025-1128 made "no new synchronous dependency on the checkout path without a
  fallback" a policy. The assistant is optional UX, so it must never sit on the render or checkout path.
- **Peak 12x**, 3,600 concurrent streams, each held open 8-12 s. Long-lived connections, low CPU per
  connection: an I/O-bound workload that scales differently from the storefront's SSR.
- **TTFT p95 1.5 s** (2.5 s at peak) and **2.5 cents average / 10 cents ceiling** per conversation,
  with 3.2 model calls per conversation.
- **Data ownership.** Catalog and orders own their data and asked that nobody new reads their DBs
  (INC-2026-0903). Orders has a monthly Q4 change window (next 2026-12-02).
- **Security.** Approved egress only, no PII to models, act with the end user's identity, confirm writes.
- **Teams.** AI team of 4 owns the assistant; platform (5) owns Kong, CDN, EKS, telemetry.

## System overview

```text
 storefront web/mobile         associate app (tablets)
        |  SSE (POST, text/event-stream)  |
        v                                  v
   CDN  -- route /api/assistant/*: no caching, no buffering, origin read timeout 120 s
        |
   Kong -- route assistant: response_buffering off, request_buffering off, upstream read timeout 90 s,
        |   auth plugin (shopper JWT / store SSO), rate limit per consumer + per user
        v
   assistant-service (AI team, Python FastAPI, own Helm release, HPA on in-flight streams)
     |-- agent loop, tools, prompt versions, evals in CI
     |-- model client module: retry/backoff/fallback/budget  --> egress proxy --> provider A / provider B
     |-- Redis (managed): per-user and per-workload token buckets, conversation state (TTL 24 h)
     |-- OpenTelemetry: gen_ai.* spans, tokens and cost per call, conversation id
     |
     |-- sync HTTP, user token forwarded --> catalog-service  (search, batch stock)      [catalog team]
     |-- sync HTTP, user token forwarded --> order-service    (order status, returns)    [orders team]

 storefront monolith (web team): renders pages without the assistant; loads the chat panel as a
 lazy client-side bundle behind a feature flag. No server-side call to the assistant.
```

Sync calls: assistant to catalog/orders (short timeouts, circuit breakers). Streaming: assistant to
browser. Nothing in the storefront's render path calls the assistant.

## ADR-1: Assistant as a separate service or a module in the storefront; catalog via API or database

**Context.** The assistant has a different load shape (thousands of long-lived streams, I/O bound), a
different release cadence (prompt and model changes several times a week, gated by evals), a different
team, and new risks (provider outages, cost runaway). The storefront monolith is Node SSR owned by the
web team, and its last incident came from a new synchronous dependency.

**Options considered.**
1. Module inside the storefront monolith (Node), calling catalog-db and orders-db directly.
2. Module inside the storefront, calling catalog-service and order-service APIs.
3. Separate assistant-service (Python) owned by the AI team, calling catalog-service and order-service
   APIs with the user's token.
4. Separate assistant-service that reads a replica of catalog-db for search speed.

**Decision.** Option 3. The assistant is its own deployable with its own scaling, on-call and budget.
It reads products and stock only through catalog-service, and orders only through order-service, with
the end user's token forwarded so those services enforce scope.

**Why not the others.** Options 1 and 4 break data ownership. They repeat INC-2026-0903 and put the
assistant on the hook for every schema change. Options 1 and 2 put a slow, failure-prone dependency
inside the monolith. Thousands of 10 s streams would tie up the monolith's event loop and memory at
peak, and every prompt change would need a storefront release. A monolith-first argument does apply to
the assistant's internals: tools, agent loop and model client stay as modules of one service. They do
not become more microservices.

**Consequences.**
- Good: independent scaling (HPA on in-flight streams, not CPU), blast radius limited to the chat
  panel, the AI team ships prompt changes behind its own eval gate, and per-feature cost is easy to
  attribute.
- Bad: one more service to operate and two more network hops per tool call (about 20-40 ms each),
  which are small next to model latency. The assistant needs two endpoints that do not exist today:
  a batch stock lookup from catalog (small, catalog releases twice a week) and associate-scoped order
  lookup from orders. That second one must make the 2026-12-02 window, or phase 1 ships without the
  associate order lookup.
- The storefront change is client-side only: a lazy-loaded panel behind a flag, with the search box
  still working without it.

**Revisit when.** The AI team owns several assistants that share 80 percent of their code, or the
latency budget forces co-location with catalog search (for example retrieval over embeddings that the
catalog team would rather own).

## ADR-2: Streaming transport (SSE vs WebSocket vs polling) through the gateway and CDN

**Context.** Answers must stream (TTFT 1.5 s vs full answer 8 s). The path is CDN, then Kong (HTTP/1.1
upstream, 30 s default timeout, buffering configurable), then the assistant. WebSocket on the CDN needs
an unbudgeted tier. Mobile networks drop connections.

**Options considered.**
1. **SSE over HTTP** (POST with a JSON body, `text/event-stream` response, read with fetch streams).
2. **WebSocket** end to end.
3. **Polling**: POST starts a job, the client polls GET for deltas every 300-500 ms.
4. Long-poll / chunked JSON lines without SSE framing.

**Decision.** SSE over HTTP POST through the existing CDN and Kong, with these route changes owned by
platform:
- CDN: `/api/assistant/stream` not cached, response buffering off, origin read timeout 120 s.
- Kong: `response_buffering=false` and `request_buffering=false` on the route, upstream read timeout
  90 s, the same auth plugin as other routes.
- The assistant sends a keepalive comment every 10 s, below every idle timeout on the path, and event
  ids on every token. On reconnect the client either resumes with `Last-Event-ID` (served from Redis,
  last 200 events, 5 min) or starts over and replaces the text. It never appends a replay.

**Why.** The traffic is one-way, server to client: the user sends a question and the model streams an
answer. SSE is plain HTTP, so Kong auth, rate limits, logs and the CDN work as they do today with two
settings flipped. WebSocket adds bidirectionality we do not need, a CDN tier we would have to buy, and
sticky connection handling in Kong and on EKS. Polling multiplies request rate at peak (3,600 streams
x 2-3 polls per second is about 10k rps of mostly empty responses) and adds up to one interval of
latency per update.

**Consequences.**
- Good: no new infrastructure; standard HTTP observability; cancel is closing the request (the server
  must stop generating on disconnect to save cost).
- Bad: one HTTP connection per active answer (HTTP/2 to the CDN removes the browser's 6-connection
  limit; Kong to upstream stays HTTP/1.1, so size the connection pools). Intermediaries that buffer
  break it silently, so add a synthetic check that measures TTFT through the real CDN path.
- Resume needs a small Redis buffer; without it a drop means a second, billed generation.

**Revisit when.** We add voice or truly bidirectional features (barge-in, live typing indicators from
agents in handoff), or the CDN tier with WebSocket becomes standard.

## ADR-3: Model fallback and rate limiting inside the assistant or in a shared LLM gateway

**Context.** INC-2026-0614 showed what goes wrong without backoff, fallback or workload-scoped keys.
Security requires approved egress and secrets-managed credentials. Today the only production consumer
is the assistant; the catalog team is interested in using a model for enrichment next year. Platform
will not run new stateful infrastructure in Q4.

**Options considered.**
1. **In-process model client library** in the assistant: retries with backoff and jitter, timeouts,
   fallback from A to B, budget guard, metering, Redis token buckets. The egress proxy is the only
   shared piece.
2. **Shared LLM gateway service** (built or adopted) that all teams call: one place for keys,
   fallback, quotas, caching, metering and audit.
3. **Provider-side features only**: rely on the provider's own retries/limits, no fallback.

**Decision.** Option 1 now, built as a separately packaged library with a provider-neutral interface
(`complete(request) -> response + usage`). Each workload gets its own key and limits. Every call emits
OpenTelemetry `gen_ai.*` attributes plus a `cost_usd` and `feature` attribute. Concretely:
- Timeouts derived from `max_tokens` and streaming idle timeouts, not a flat 10 s.
- Retry only 429/529/5xx and connection errors before the first byte, at most 2 attempts, exponential
  backoff with jitter, honor `retry-after`.
- Fallback to provider B on provider A outage or circuit open, at most once per call. B gets its own
  prompt variant that is evaluated in CI, because the API shapes differ.
- Per-conversation budget guard: stop and answer "I can't help with that right now" before the 10 cent
  ceiling. Per-user and per-workload token buckets live in Redis.

**Why not a gateway now.** With one consumer, a shared gateway adds a network hop to the latency budget,
a new service with no owner (platform said no for Q4) and a single point of failure in front of every
model call, while solving a coordination problem we do not have yet. Provider-only (option 3) fails
INC-2026-0614 again.

**Consequences.**
- Good: fastest path, fewest hops, the AI team controls the failure behaviour it is on call for.
- Bad: when a second team needs a model, they either reuse the library (versioned, but keys and quotas
  are per service) or we extract a gateway. Cross-team quota sharing on one provider account is not
  enforced centrally until then; mitigate with separate provider projects/keys per workload.

**Revisit when.** A second production consumer appears, or security asks for central prompt/response
audit across teams, or we want cross-team semantic caching. At that point extract the library into a
gateway service owned by platform, keeping the same interface so the assistant changes one import.

## How it fails

| Failure | Blast radius | Detection | User sees | Mitigation |
|---|---|---|---|---|
| Provider A down or 529s | assistant only | error rate by provider, circuit breaker state | answer from provider B, slightly different wording | fallback once, evaluated B prompt, alert on fallback ratio |
| Provider rate limit (429) | assistant only | 429 counter, token bucket rejections | slower answer or "busy, try again" | backoff with retry-after, per-user buckets shed abusive users first |
| Catalog slow | assistant product answers | tool span latency, catalog breaker | answer without stock ("check the product page") | 800 ms tool timeout, batch stock call, deadline propagation |
| Orders down or change window | order questions | tool errors | "I can't look up orders right now; here is the order page" | tool returns is_error, model is told; handoff link |
| Assistant down | chat panel only | synthetic TTFT check, Kong 5xx | panel hidden or "assistant unavailable"; search box works | feature flag kill switch, lazy-loaded panel, no server-side dependency |
| Peak 12x | assistant and providers | in-flight streams, TTFT p95 | slower TTFT, then "busy" under shedding | HPA on in-flight streams, pre-scale for Black Friday, provider quota raise ahead of time, budget guard |
| Bad prompt change | all answers | eval suite in CI, online grounding check rate | wrong or ungrounded answers | prompt versions behind a flag, eval gate, instant rollback by version |
| Cost runaway (retry loop, long prompts) | budget | cost per conversation metric, daily spend alert | nothing until the guard triggers | per-conversation ceiling, attempt cap, alert at 2x average |

## Cost and latency budget

Typical answer, p50: Kong and CDN about 30 ms, agent loop first model call TTFT about 700 ms, one tool
round trip about 60 ms plus a second model call TTFT 600 ms before the answer streams. TTFT is about
1.4 s p50, which is why the tool loop should be kept to one or two calls before streaming and why
prompt caching of the static system prompt and tool definitions matters (it cuts the second call's
TTFT and input cost).

Money: 3.2 calls x (about 3,000 input tokens, mostly cached, + 250 output tokens) is about 2 cents at
provider A list prices with caching; without caching about 3.5 cents. Fallback to B is cheaper. The
ceiling is enforced in code, not hoped for.

## Open questions

- Catalog: can they ship a batch stock endpoint (`POST /inventory/lookup` with up to 50 SKUs) before
  peak? If not, cap the assistant to 3 SKUs per stock answer.
- Orders: associate-scoped order lookup for the 2026-12-02 window; otherwise the associate app ships
  without order lookup in phase 1.
- Platform: Kong and CDN route settings for streaming, and a synthetic TTFT probe through the CDN.
- Security: sign-off that SKUs and order ids are not PII in this context; redaction of free text.
- Prototype first: SSE through the real CDN and Kong path with a fake model, to prove buffering is off.

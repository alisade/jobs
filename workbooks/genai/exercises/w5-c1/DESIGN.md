# Design: shopping assistant service boundaries (three ADRs)

<!-- Audience: the architecture review board (catalog, orders, web, platform leads, security).
Use inputs/. Each ADR: Context, Options considered (at least three where it makes sense), Decision,
Consequences (good and bad), and Revisit when. Diagrams in ```text or ```mermaid. Name real mechanisms
(Kong route settings, CDN buffering, Redis, OpenTelemetry attributes, circuit breakers). -->

## Context and drivers

<!-- The few drivers that decide these ADRs: peak 12x, TTFT target, cost ceiling, data ownership,
fail-soft, approved egress, team sizes and release cadence. -->

## System overview

<!-- Diagram of the target: clients, CDN, Kong, assistant, catalog, orders, model providers via egress,
Redis, telemetry. Show which calls are sync, which stream, and who owns each box. -->

## ADR-1: Assistant as a separate service or a module in the storefront; catalog via API or database

<!-- Context / Options considered / Decision / Consequences / Revisit when -->

## ADR-2: Streaming transport (SSE vs WebSocket vs polling) through the gateway and CDN

<!-- Context / Options considered / Decision / Consequences / Revisit when. Include what must change in
Kong and the CDN, keepalives, and what happens on a dropped connection. -->

## ADR-3: Model fallback and rate limiting inside the assistant or in a shared LLM gateway

<!-- Context / Options considered / Decision / Consequences / Revisit when. Retries, backoff, fallback
model, per-workload keys and limits, cost metering, who operates it. -->

## How it fails

<!-- Table: failure | blast radius | detection | behaviour the user sees | mitigation.
At least: provider A down, provider rate limited, catalog slow, orders down, assistant down,
peak traffic, a prompt change that breaks answers. -->

| Failure | Blast radius | Detection | User sees | Mitigation |
|---|---|---|---|---|
|  |  |  |  |  |

## Cost and latency budget

<!-- Where the time goes for a typical answer (TTFT) and where the money goes per conversation; how the
design keeps both inside the targets at peak. -->

## Open questions

<!-- What you need from other teams, and what you would prototype first. -->

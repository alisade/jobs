# kestrel-assistant 2026.11.20

- Answer cache in front of the agent for the holiday peak. Identical questions (after normalization)
  are served from Redis for 24 h without calling the model. Load test: 61% hit rate, model spend -40%,
  p95 latency 2.3 s -> 0.4 s on hits.
- Associate app: store id is now sent with every question (used by check_inventory).

# Reference: backend/w5-t1 Duplicate stage-change events after the relay restart

Injected fault: `outbox/relay.py` sets `headers["event_id"] = str(uuid.uuid4())` when publishing. Every
republish of a row looks like a new event, so the consumer's processed-event dedupe never fires.
Contributing: rows are marked sent once per batch (a kill republishes the whole published prefix), and
the claim is SELECT-then-UPDATE without ownership checks. The fixed relay is in
`.grading/solution/outbox/relay.py`, the model answer in `.grading/solution/ANSWER.md`.

The lesson: an outbox relay is at-least-once by nature; correctness comes from a stable event identity
created in the business transaction and an idempotent consumer. Exactly-once is an end-to-end property,
not a relay feature.

## Interview angles
- "Can the relay be exactly-once?" (Not across the DB and the broker without a shared transaction;
  Kafka transactions cover Kafka-to-Kafka. Make the consumer idempotent.)
- "Polling relay or Debezium?" (Polling is simple and good to moderate volume; CDC removes polling load
  and lag, adds a connector to operate.)
- "How do you shut a relay down cleanly in Kubernetes?" (Stop claiming on SIGTERM, finish the in-flight
  row, release unpublished claims, keep the batch time under the grace period.)

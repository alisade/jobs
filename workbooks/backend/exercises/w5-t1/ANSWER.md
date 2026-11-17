# ANSWER: backend/w5-t1 Duplicate stage-change events after the relay restart

## Approach

<!-- How you investigated: what you compared across the relay logs, the consumer log and the dump. -->

## Root cause

<!-- The defect (and the trigger), with evidence: log lines, dump rows, make repro output. Say what part
of what happened is normal at-least-once behavior. Address the broker restart. -->

## Fix

<!-- What you changed in relay.py and how you verified it. -->

## Trade-offs / what I would do in production

<!-- Short: batch size vs grace period, lease length, CDC (Debezium) instead of polling, a Kafka header
contract for event ids, alerts. -->

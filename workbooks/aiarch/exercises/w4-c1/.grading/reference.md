# Reference: aiarch/w4-c1

See `.grading/solution/obo/exchange.py`. The decisive checks: RS256 only and kid lookup (blocks
alg confusion and foreign keys); audience on both tokens; sub of the issued token equals the
user (blocks an IdP that issues a service token); scope subset (blocks over-broad grants);
act.sub equals the agent; cache keyed per user. Clock-driven exp checks keep tests
deterministic.

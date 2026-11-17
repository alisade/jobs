# Reference: aiarch/x-1

Root cause: GSI `by-status` keyed on status (one value, ACTIVE, for all open sessions) is a hot
partition; GSI write throttling back-pressures base-table writes. Fix: sparse, write-sharded
index key ACTIVE#0..9 by a stable hash, removed on close; fan-out query across shards.

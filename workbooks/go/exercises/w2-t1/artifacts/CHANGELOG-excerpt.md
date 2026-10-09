## v1.14.0 (2026-10-01)
- perf: reuse compression buffers via sync.Pool; cuts allocations per batch by ~40%.
- fix: enforce SendTimeout per attempt inside the shipper. The vendor bulk client does not
  honour context cancellation, so a brownout used to stall every tailer for 30s+.
- chore: bump vendor bulk SDK 3.8.1 -> 3.9.0.

## v1.13.4 (2026-08-20)
- fix: drop lines longer than 256 KiB instead of failing the batch.

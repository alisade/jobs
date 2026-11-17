# ANSWER: edgefde/x-2 Spikes at every chunk boundary

## Approach

Every chunk alerts with nearly the same score on every pump, so the cause is in the pipeline, not
the machines. The first filtered samples of a chunk show large ringing that decays within a few
hundred samples, then plain noise.

## Root cause

`process` runs `sosfilt` with no initial state on each chunk. The DC-coupled sensor carries +1 g of
gravity, so every chunk looks to the filter like a step from 0 to 1 g; the band-pass rings at every
boundary. Those samples dominate the fourth moment: kurtosis 12-15, crest 17, every chunk
(`gateway.log`). The clock drift warning (180 ppm) shifts frequencies by 0.018% and appears once; it
cannot make once-per-chunk impulses.

## Fix

Carry `zi` across calls, initialise it with `sosfilt_zi(sos) * x[0]` on the first chunk, clear it in
`reset()`. Verified that chunk sizes 20000, 4096 and 777 give output identical to one-shot filtering,
healthy streams are quiet and the faulty stream alerts every chunk.

## Trade-offs / what I would do in production

Zero-phase filtering is offline only; on the stream accept the causal filter's group delay. After a
gap or reconnect call `reset()` so stale state does not ring. Add a chunk-size invariance test to CI
for every streaming transform.

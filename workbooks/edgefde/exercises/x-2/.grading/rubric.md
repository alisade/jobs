# Rubric: edgefde/x-2 Spikes at every chunk boundary in the streaming band-pass
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: `sosfilt` is called with zero initial state on every chunk, so each chunk starts as if the input jumped from 0 to the +1 g gravity offset (plus the shaft tone): a step that rings the band-pass at every boundary, which inflates kurtosis and crest of the chunk. Partial: "filter resets" without the DC step mechanism. |
| 3 | Evidence | 10 | first_chunk_samples.csv: large ringing in the first few hundred samples decaying to the noise level; gateway.log: every chunk alerts with near-identical scores, independent of the pump. |
| 4 | Red herring | 10 | Clock drift of 180 ppm shifts frequencies by 0.018% and does not produce per-chunk impulses; it appears once, the alerts are every chunk. |
| 5 | Fix | 10 | State zi carried between chunks, initialised with sosfilt_zi * x[0], reset() clears it; not filtfilt per chunk (non-causal and still has edge effects). |
| 6 | Production notes | 10 | Group delay of a causal filter, handling gaps and reconnects (reset and re-initialise), chunk-size invariance test in CI, high-pass or DC removal as part of the chain. |
Total: 100

# Rubric: edgefde/w2-t1 Phantom fault peak on the new pumps
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: `x[::5]` decimates without a low-pass; at 2 kHz the Nyquist frequency is 1 kHz, so the 44 x 29.5 = 1298 Hz gear mesh (present because the MEMS sensor has no analog anti-alias filter and the 10 kHz stream carries it) folds to 2000 - 1298 = 702 Hz, inside the 600-900 Hz band. Only the gearbox pumps P07-P10 have a mesh. Partial: "aliasing" without the arithmetic or without why only P07-P10. |
| 3 | Evidence | 10 | Alert lines all at 702.0 Hz for P07-P10 vs 772 Hz for P03; a raw 10 kHz spectrum showing the 1298 Hz line and no 702 Hz line; gateway.yaml "analog_antialias_filter: none". |
| 4 | Red herring | 10 | The 1.6x gain scales every bin equally, so a ratio-to-median score does not change, it rolled out to all gateways (old pumps are quiet), and gain cannot create a new frequency. |
| 5 | Fix quality | 10 | resample_poly or decimate (FIR) or an explicit low-pass below 1 kHz before dropping samples; verified with a tone sweep; detector untouched. |
| 6 | Production notes | 10 | CPU/latency of the filter on the gateway, streaming state across chunks, ask the vendor for the internal digital filter settings (many MEMS parts have a configurable output data rate filter), watching the mesh needs fs > 2 x 1298 Hz plus margin (for example keep 5 kHz or more), a tone-injection test in CI. |
Total: 100

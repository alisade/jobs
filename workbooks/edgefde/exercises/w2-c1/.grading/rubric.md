# Rubric: edgefde/w2-c1 Spectral features and bearing-fault detection
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Signal reasoning | 20 | Full: ANSWER.md explains impacts ringing a resonance (amplitude modulation), why the raw spectrum shows energy near 3.2 kHz instead of a line at BPFO, why the envelope recovers the repetition rate, and why the 2x harmonic check cuts false alarms. Partial: correct code, thin explanation. |
| 3 | Numerical care | 10 | Window applied before the FFT, mean removed, parabolic (or equivalent) interpolation, PSD scaling understood (density vs spectrum), resolution = fs/nperseg stated. |
| 4 | Code quality | 5 | Shared input validation, typed, no magic numbers without a name or comment. |
| 5 | Production notes | 10 | Varying shaft speed (order tracking / tachometer), band selection (spectral kurtosis), streaming filter state, validation on CWRU or plant data, threshold set from a false-alarm budget. |
Total: 100

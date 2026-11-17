# ANSWER: edgefde/w2-c1 Spectral features and bearing-fault detection

## Approach

Built each function against a known answer from `vib/synth.py`: a 50 Hz sine for RMS, crest factor
and kurtosis, a 120 Hz tone for PSD resolution, a 123.4 Hz tone for sub-bin frequency, then the
bearing signals for the detector. Measured detector scores over 20 seeds per class before picking
the threshold.

## Fix

A defect hits once per ball pass. Each hit rings the housing resonance near 3.2 kHz and dies out in
a few milliseconds, so the raw spectrum shows a hump around the resonance with sidebands at BPFO
spacing, not a line at 105.75 Hz. Band-passing around the resonance and taking the Hilbert envelope
keeps only "how loud is the ringing over time", which repeats at BPFO, so the envelope spectrum has
a clean line at BPFO and 2x BPFO. Healthy captures produce random envelope peaks up to about 9 dB
over the local median; faults score 17-28 dB. Requiring the 2x harmonic as well removes the single
random peaks; 12 dB sits in the gap.

## Trade-offs / what I would do in production

Shaft speed drifts with load, so track it (tachometer or a speed estimate from the 1x line) and
recompute BPFO per window or resample to orders. Pick the demodulation band per machine with
spectral kurtosis instead of a fixed 2-4.5 kHz. On the gateway, use causal filters with state across
windows. Validate on CWRU data first, then on the plant's own captures, and set the threshold from an
agreed false-alarm budget per machine-week.

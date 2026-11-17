# edgefde/w2-c1 - Spectral features and bearing-fault detection

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 2 (Mon: sampling and the FFT; Tue: windowing and Welch PSD; Wed: filters and envelopes; Thu: features and bearing frequencies)

## Scenario

Corvane Industrial's Dunmore plant (fictional) runs ten centrifugal pumps on 6205-class deep-groove
bearings (9 balls, ball diameter 7.94 mm, pitch diameter 39.04 mm, contact angle 0) at a shaft speed of
29.5 Hz. Accelerometers on the bearing housings sample at 20 kHz. The reliability lead wants a feature
module the edge gateway can run on every 2-second window: the usual time-domain health numbers, band
energies for the dashboard, and an early-warning flag for outer- and inner-race defects that does not
fire on healthy pumps.

Bearing defects show up as a train of short impacts at the defect frequency. Each impact rings a
structural resonance (here about 3.2 kHz), so in the raw spectrum you see a hump near the resonance,
not a line at BPFO. Envelope analysis (band-pass around the resonance, Hilbert envelope, spectrum of
the envelope) recovers the repetition rate. `vib/synth.py` generates signals with exactly this
structure, with known frequencies, so every function can be tested against a known answer.

## What you have

| Path | What it is |
|---|---|
| `vib/features.py` | The module you implement (signatures and contracts as stubs) |
| `vib/synth.py` | Synthetic signals: `tones(...)` and `bearing_signal(...)` (do not edit) |
| `scripts/report.py` | `make report`: confusion table over 30 synthetic captures |

## Your task (the contract)

| Function | Contract |
|---|---|
| `time_features(x)` | AC features (mean removed first): `rms`, `peak` (max abs), `crest_factor` = peak/rms, `kurtosis` (Pearson: Gaussian = 3, sine = 1.5) |
| `welch_psd(x, fs, nperseg=4096)` | `scipy.signal.welch`, Hann window, 50% overlap, constant detrend, density scaling; `nperseg` capped at `len(x)` |
| `frequency_resolution(fs, nperseg)` | `fs / nperseg` |
| `band_energies(f, pxx, bands)` | PSD integrated over each `[lo, hi)`: a sine of amplitude A gives about A^2/2 in its band |
| `dominant_frequency(x, fs, fmin=1)` | strongest component above `fmin`, within a quarter bin (`fs/len(x)`), DC ignored; use a window and interpolate between bins |
| `bearing_frequencies(shaft_hz, n_balls, ball_d, pitch_d, contact_deg)` | BPFO, BPFI, BSF, FTF with the standard formulas (r = d/D cos(angle)); ValueError on impossible geometry |
| `envelope_spectrum(x, fs, band)` | 4th-order Butterworth band-pass (zero-phase is fine offline), Hilbert envelope, mean removed, windowed amplitude spectrum; ValueError if the band is not inside (0, fs/2) |
| `detect_bearing_fault(x, fs, shaft_hz, geometry, band, tol, snr_db)` | score = 20 log10(max envelope magnitude within +/- tol of the target / median magnitude in 0.6x-1.4x of the target excluding that window); a defect is flagged when the fundamental scores >= `snr_db` and its 2x harmonic >= `snr_db - 3`; if both qualify, the higher score wins. Return `FaultReport` |

All functions raise `ValueError` on NaN/infinity, non-1-D input, windows shorter than 64 samples, or
`fs <= 0`.

## Acceptance criteria (what the grader checks)

- Known answers: sine and Gaussian kurtosis, crest factor, DC offset ignored, PSD resolution, band
  power of a sine within 5%, dominant frequency within 0.25 Hz at 1 Hz bins, bearing frequency
  identities (BPFO + BPFI = n x shaft speed) with a contact angle.
- Healthy captures (6 seeds) are never flagged; outer and inner race faults (including a weak one) are
  found and labelled correctly.
- Input validation, including a band above Nyquist.
- `ANSWER.md` explains in plain words why the raw spectrum does not show BPFO and the envelope does,
  and what you would change for a real sensor (sample rate, anti-alias filter, shaft speed tracking).

## How to run

```bash
make setup
make test      # visible tests
make report    # healthy vs outer vs inner
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/w2-c1
make clean
```

## What to submit

`vib/features.py` and a filled-in `ANSWER.md`.

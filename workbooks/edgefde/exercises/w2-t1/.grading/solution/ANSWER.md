# ANSWER: edgefde/w2-t1 Phantom fault peak on the new pumps

## Approach

Read the alert board first: every P07-P10 alert is at exactly 702.0 Hz, while P03's are at 772 Hz.
A frequency that is identical across four machines and never moves looked like an artefact, not a
bearing. Then I checked the asset notes and took a spectrum of a raw 10 kHz capture of P07.

## Root cause

`edge/preprocess.py` reduces 10 kHz to 2 kHz with `x[::5]`, with no low-pass first. At 2 kHz the
Nyquist frequency is 1 kHz, so every component between 1 and 5 kHz folds back into 0-1 kHz.
P07-P10 are gearbox driven: 44-tooth pinion x 29.5 Hz shaft = 1298 Hz gear mesh. 2000 - 1298 =
702 Hz, which is inside the 600-900 Hz outer-race band:

```text
2026-10-27T06:00:00 ALERT pump=P07 outer_race_band peak=702.0Hz score=51.5dB
2026-10-27T06:00:00 ALERT pump=P03 outer_race_band peak=772.0Hz score=43.4dB
```

The raw P07 capture has a line at 1298 Hz and nothing at 702 Hz, and gateway.yaml says the MEMS
sensor has no analog anti-alias filter, so the alias is created by our software decimation.

The firmware gain change is not involved: a 1.6x gain scales every bin, the detector scores the peak
against the spectrum median so the gain cancels, it rolled out to all gateways while P01-P06 stay
quiet, and a gain cannot move energy to a new frequency.

## Fix

`downsample` now uses `scipy.signal.resample_poly(x, 1, factor)`, a polyphase FIR low-pass at the
output Nyquist followed by decimation. Verified: `make run` shows P07-P10 quiet and P03 still at
772 Hz; a 1298 Hz tone comes out about 80 dB down at 702 Hz; 100, 300 and 772 Hz pass within 0.01 dB.

## Trade-offs / what I would do in production

On the gateway the filter must run on a stream: a causal FIR with state carried between chunks,
which adds a fixed group delay (fine for alerting). Ask the sensor vendor to enable the part's
internal digital low-pass for the configured output rate. To monitor the gearbox, keep at least
5 kHz and look at the mesh sidebands. Add a tone-injection test (tones above 1 kHz must not appear in
any analysis band) to CI so a future "optimisation" cannot reintroduce this.

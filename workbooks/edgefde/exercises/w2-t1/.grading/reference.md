# Reference: edgefde/w2-t1

Root cause: `downsample` picks every 5th sample of the 10 kHz stream. That is decimation without an
anti-alias filter. After decimation the Nyquist frequency is 1 kHz, and anything between 1 and 5 kHz
folds back: a tone at f appears at |f - k x 2000| for the nearest k. P07-P10 are gearbox driven with a
44-tooth pinion on the 29.5 Hz shaft: gear mesh 44 x 29.5 = 1298 Hz, which folds to 2000 - 1298 =
702 Hz, inside the 600-900 Hz outer-race band and 50 dB over the median. The MEMS sensor has no analog
anti-alias filter (gateway.yaml), so the 10 kHz stream carries the mesh honestly; the damage is done
in software. P03's real defect mode is at 772 Hz, below the new Nyquist, and survives either way.

Red herring: firmware 3.4.0 multiplied raw amplitudes by 1.6. The detector scores a peak relative to
the spectrum median, so a uniform gain cancels; it also went to every gateway and the direct-drive
pumps stayed quiet; and no gain change can create a line at a new frequency.

Fix (`.grading/solution/edge/preprocess.py`): `scipy.signal.resample_poly(x, 1, 5)` (polyphase FIR,
Kaiser window, cutoff at the output Nyquist), which attenuates 1298 Hz by about 80 dB and passes
772 Hz within 0.01 dB. `signal.decimate(x, 5, ftype="fir")` (about 64 dB) is also fine.

Production: on the gateway use a causal FIR or IIR low-pass with state carried across chunks
(zero-phase filtering needs the whole signal). Ask the sensor vendor how to enable the part's internal
digital low-pass at the configured output data rate. To monitor the mesh itself you need fs well above
2 x 1298 Hz (5 kHz or more) and to look at sidebands around it. Add a tone-injection test (sweep
tones above Nyquist, assert nothing lands in the analysis bands) to the pipeline CI.

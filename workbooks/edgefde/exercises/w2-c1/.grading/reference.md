# Reference: edgefde/w2-c1

The reference implementation is `.grading/solution/vib/features.py` (about 120 lines).

- `time_features`: subtract the mean first; Pearson kurtosis m4/m2^2 (sine 1.5, Gaussian 3, impulsive >> 3).
- `welch_psd`: `scipy.signal.welch(window="hann", noverlap=nperseg//2, detrend="constant", scaling="density")`.
  Band energy is `sum(pxx[band]) * df`, so a sine of amplitude A integrates to about A^2/2.
- `dominant_frequency`: Hann window, rfft, zero bins below fmin, parabolic interpolation on log
  magnitudes around the peak bin (error well under 0.1 bin for a Hann window).
- `bearing_frequencies`: r = (d/D) cos(phi); BPFO = n/2 fr (1 - r); BPFI = n/2 fr (1 + r);
  BSF = D/(2d) fr (1 - r^2); FTF = fr/2 (1 - r). For the 6205 at 29.5 Hz: 105.75 / 159.75 / 69.52 / 11.75 Hz.
- `envelope_spectrum`: Butterworth band-pass 2-4.5 kHz as SOS with `sosfiltfilt`, `abs(hilbert(y))`,
  remove the mean (else a huge DC line), Hann window, amplitude spectrum.
- Detector: peak within +/-3% of the target over the median of the 0.6x-1.4x neighbourhood; requiring
  the 2x harmonic removes the random noise peaks that otherwise cross 8-9 dB on healthy captures.
  Measured on 20 seeds: healthy max 9.3 dB, weak outer 17-20 dB, outer 26-28 dB, inner 22-24 dB, so
  12 dB leaves margin on both sides.

Why the envelope: an impact every 1/BPFO seconds excites a resonance that decays within a few ms. The
energy sits near the resonance; BPFO appears only as sidebands spaced at BPFO around it. Demodulating
(the envelope) turns those sidebands into a line at BPFO and its harmonics.

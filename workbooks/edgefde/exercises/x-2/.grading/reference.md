# Reference: edgefde/x-2

`StreamingBandpass.process` calls `sosfilt` without `zi`, so every 1-second chunk is filtered from a
zero state. The sensor is DC-coupled and mounted vertically: every sample carries about +1 g. To the
filter each chunk therefore starts with a step from 0 to 1 g (plus the shaft tone phase), and a
4th-order band-pass rings for a few hundred samples. Those few hundred large samples dominate the
fourth moment: kurtosis 12-15 and crest 17 on a healthy pump, every chunk.

Fix: keep `zi` between calls (`y, self.zi = sosfilt(self.sos, x, zi=self.zi)`), initialise it on the
first chunk to the steady state for the first sample (`sosfilt_zi(sos) * x[0]`), and clear it in
`reset()`. Output is then identical to filtering the whole stream at once, for any chunk size.
`sosfiltfilt` per chunk is wrong twice: it is non-causal (needs future samples) and still pads each
chunk edge.

Red herring: 180 ppm drift moves a 3.2 kHz resonance by 0.6 Hz; it cannot create once-per-chunk
impulses.

# edgefde/x-2 - Spikes at every chunk boundary in the streaming band-pass (optional)

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 7 add-on (field drills); Week 2 (Wed: filters, "why streaming filters need state")

## Scenario

A second Corvane site (fictional) moved the impact detector from batch captures to the live stream:
the sensor driver hands the gateway 1-second chunks at 20 kHz, the gateway band-passes each chunk
(500 Hz - 4 kHz Butterworth) and scores kurtosis and crest factor per chunk. The site's controls
engineer reports:

> "Since the switch to streaming, every pump alerts every single second, kurtosis 12-15, crest 17,
> even a pump we just rebuilt. The batch version was fine. The driver also complains about clock
> drift. Did the sensor go bad?"

## What you have

| Path | What it is |
|---|---|
| `incident/gateway.log` | 30 s of per-chunk scores from a healthy pump |
| `incident/first_chunk_samples.csv` | the first 400 filtered samples of a chunk |
| `stream/filter.py` | the streaming band-pass (edit) |
| `stream/alerting.py` | per-chunk scoring (do not edit) |
| `scripts/sensor.py` | synthetic DC-coupled stream with gravity, shaft tone and noise (do not edit) |
| `scripts/run.py` | `make run` |

## Your task

1. Find why healthy pumps alert on every chunk; show it with the samples around a chunk start.
2. Rule the clock-drift warning in or out.
3. Fix `StreamingBandpass` so the chunk size is invisible in the output, and `reset()` really forgets
   history (used after a sensor reconnect).

## Acceptance criteria (what the grader checks)

- For chunk sizes 20000, 4096 and 777, the concatenated output equals one-shot causal filtering of the
  whole stream, `sosfilt(sos, x, zi=sosfilt_zi(sos) * x[0])`, within 1e-9.
- Causal (no output before an impulse arrives), no transient at chunk edges, empty chunks allowed.
- Healthy streams never alert; a faulty stream alerts every chunk; `reset()` restarts from steady state.
- `ANSWER.md`: root cause with evidence, red herring, why zero-phase filtering cannot be used here.

## How to run

```bash
make setup && make run && make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/x-2
make clean
```

## What to submit

`stream/filter.py` and a filled-in `ANSWER.md`.

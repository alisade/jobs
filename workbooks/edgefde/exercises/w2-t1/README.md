# edgefde/w2-t1 - Phantom fault peak on the new pumps

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 2 (Mon: sampling, Nyquist and aliasing; Wed: filters)

## Scenario

The maintenance planner at Corvane Industrial's Dunmore plant (fictional) opens a ticket:

> "Since last week the outer-race early warning fires on all four NEW pumps, P07-P10, every capture,
> always at 702 Hz. Those pumps were installed three weeks ago with brand-new bearings. P03 also
> alerts, but P03 really had a bad bearing (WO-55812). The gateway firmware went to 3.4.0 the same
> week and changed the accelerometer gain; can you check whether that broke the detector? We are one
> false alarm away from the plant turning the whole thing off."

The detector (`edge/detector.py`) was tuned and signed off by the reliability team and must not change.
The sensor samples at 10 kHz; the gateway reduces the stream to 2 kHz (`edge/preprocess.py`) before the
detector runs. `make setup` runs today's captures through the pipeline and writes the evidence.

## What you have

| Path | What it is |
|---|---|
| `incident/alerts.log` | today's alert board, 3 captures per pump |
| `incident/firmware-changelog.txt` | what changed in firmware 3.4.0 |
| `incident/gateway.yaml` | sensor and asset configuration |
| `edge/preprocess.py` | 10 kHz to 2 kHz reduction (edit) |
| `edge/detector.py` | the signed-off detector (do not edit) |
| `scripts/plant.py` | raw 10 kHz captures per pump, with the asset notes (do not edit) |
| `scripts/run.py` | `make run`: the alert board through your current code |

## Your task

1. Find why the new pumps alert. Prove it with numbers: where does 702 Hz come from? Use the sample
   rates, the asset notes and a spectrum of the raw capture (a few lines of NumPy are enough).
2. Decide whether the firmware gain change is involved.
3. Fix the pre-processing so the new pumps are quiet and P03 still alerts, without touching the
   detector, the 2 kHz output rate or the band.
4. Say what you would ask the sensor vendor and what the safe sample rate would be if the plant ever
   wanted to watch the gear mesh itself.

## Acceptance criteria (what the grader checks)

- P07-P10 not flagged (several captures), P01-P06 quiet, P03 still flagged at about 772 Hz.
- A 1298 Hz tone in the 10 kHz stream shows at least 40 dB below its input level at 702 Hz after
  reduction; tones at 100, 300 and 772 Hz pass within 1 dB.
- Output length unchanged (2 kHz), detector constants unchanged.
- `ANSWER.md`: the aliasing explained with the Nyquist numbers, the red herring ruled out with a reason.

## How to run

```bash
make setup     # venv + incident/
make run       # alert board through your current code
make test      # visible checks
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/w2-t1
make clean
```

## What to submit

`edge/preprocess.py` and a filled-in `ANSWER.md`.

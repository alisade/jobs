# edgefde/w4-t1 - INT8 model misses faults on the gateway

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 4 (Wed: INT8 quantization and calibration; Fri: ONNX Runtime on IoT and edge)

## Scenario

Corvane Industrial (fictional) switched its 10 pump gateways from the FP32 anomaly model to INT8 on
2026-11-02 to free memory for the PLC data logger. On 2026-11-03 the maintenance planner writes:

> "A vibration route found an outer-race fault on DUN-P007 this afternoon. The edge system did not
> raise a single alert on any pump today. Before the switch we were getting a few hundred a day.
> Is INT8 just not accurate enough? The release log has warnings about IR versions and pre-processing,
> and the gateway says XNNPACK is missing. Do we roll back to FP32?"

`make setup` trains the model, runs the team's release script `edge/quantize.py` exactly as the release
did, and scores one gateway day with the real gateway runtime (`edge/gateway.py`).

## What you have

| Path | What it is |
|---|---|
| `incident/release-quantize.log` | output of the release script, with the warnings |
| `incident/gateway-eval.txt` | one gateway day scored with FP32 and INT8 |
| `incident/gateway-dun-p007.log` | the edge agent log on the faulty pump |
| `edge/quantize.py` | the team's release script (edit) |
| `edge/gateway.py` | what the gateway runs: scaler then model (correct; do not edit) |
| `scripts/inspect_qdq.py` | `make inspect`: scale and zero point of every QuantizeLinear |
| `scripts/gateway_eval.py` | `make run` scores a day after rebuilding |
| `artifacts/`, `data/`, `build/` | the model, scaler, calibration and gateway data, and the built models |

## Your task

1. Decide whether INT8 is "not accurate enough" or something else is wrong. Find the root cause and
   prove it with numbers from the model files (what range can the INT8 input actually represent, and
   what range does the gateway feed it?).
2. Rule the warnings in or out.
3. Fix the release script so INT8 detects like FP32, and say how you verified it.
4. Say what you would put in the release pipeline so this cannot ship again.

## Acceptance criteria (what the grader checks)

- With your `edge/quantize.py`, INT8 on the gateway day is within 0.02 recall and 0.01 false-alarm rate
  of FP32, with a similar alert volume.
- The INT8 input quantization range fits the gateway's standardized features, derived from the shipped
  `scaler.json`.
- The model is still static INT8 (activations quantized, QDQ) and still under 0.6x the FP32 size.
- `ANSWER.md`: root cause with evidence from `make inspect` and the data, red herrings, prevention.

## How to run

```bash
make setup     # train, release, score: evidence in incident/
make inspect   # QuantizeLinear scales of the INT8 model
make run       # rebuild with your edge/quantize.py and score the day again
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/w4-t1
make clean
```

## What to submit

Your change to `edge/quantize.py` and a filled-in `ANSWER.md`.

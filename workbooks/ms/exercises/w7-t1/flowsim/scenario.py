"""Replays Tuesday 2026-10-06 (procurement's approval day) through a flow definition.

`simulate(definition)` returns per-PO outcomes. `write_incident(definition, out_dir)` writes the
evidence bundle that `make setup` produces from the flow you have in solution/Workflows/.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import pathlib
import random
import zlib

from flowsim.engine import run_flow

DAY0 = dt.datetime(2026, 10, 6, 6, 0, 0, tzinfo=dt.timezone.utc)
FLOW_NAME = "Contoso Parts - PO sync"
WORKFLOW_FILE_GLOB = "ContosoPartsPOSync-*.json"


def ts(seconds: float) -> str:
    return (DAY0 + dt.timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def load_definition(root: pathlib.Path) -> dict:
    files = sorted((root / "solution" / "Workflows").glob(WORKFLOW_FILE_GLOB))
    if len(files) != 1:
        raise SystemExit(f"expected exactly one {WORKFLOW_FILE_GLOB} in solution/Workflows, found {len(files)}")
    return json.loads(files[0].read_text())["properties"]["definition"]


def _events():
    """Approved POs plus draft/submitted edits (which the trigger condition filters out)."""
    rnd = random.Random(20261006)
    approved = []
    # three approval bursts (procurement batch-approves) plus a trickle during the day
    for burst_start, n in ((3600 * 1 + 120, 34), (3600 * 5 + 300, 41), (3600 * 9 + 60, 29)):
        for i in range(n):
            approved.append(burst_start + i * rnd.uniform(0.8, 1.6))
    for _ in range(36):
        approved.append(rnd.uniform(0, 3600 * 11))
    approved.sort()
    pos = [{"t": t, "contoso_ponumber": f"PO-26-{4100 + i:05d}", "statuscode": 100000003,
            "contoso_purchaseorderid": f"{rnd.getrandbits(32):08x}-4c1d-f011-b4cb-000d3a5c{rnd.getrandbits(16):04x}",
            "contoso_suppliercode": rnd.choice(["SUP-ACME", "SUP-FABRIKAM", "SUP-NORTHWIND", "SUP-LITWARE"])}
           for i, t in enumerate(approved)]
    others = [{"t": rnd.uniform(0, 3600 * 11), "statuscode": rnd.choice([1, 100000001, 100000002]),
               "contoso_ponumber": f"PO-26-{6000 + i:05d}"} for i in range(37)]
    return pos, others


class ContosoPartsApi:
    """APIM in front of the Contoso Parts function: rate-limit-by-key 20 calls / 60 s per caller.
    Calls inside a full window get 429 with Retry-After = seconds to the window reset."""

    LIMIT, PERIOD = 20, 60

    def __init__(self) -> None:
        self.windows: dict[int, int] = {}
        self.received: dict[str, float] = {}
        self.log: list[str] = []

    def __call__(self, action_name, inputs, clock, trigger_body):
        host = inputs.get("host", {}) if isinstance(inputs, dict) else {}
        if host.get("operationId") != "SubmitPurchaseOrder":
            return 200, {}, {"value": []}
        w = int(clock // self.PERIOD)
        used = self.windows.get(w, 0)
        po = trigger_body.get("contoso_ponumber")
        if used >= self.LIMIT:
            retry_after = int((w + 1) * self.PERIOD - clock) + 1
            self.log.append(f"{ts(clock)} apim-contoso-parts POST /api/purchase-orders 429 0ms "
                            f"caller=power-platform policy=rate-limit-by-key remaining=0 retry-after={retry_after} po={po}")
            return 429, {"Retry-After": str(retry_after), "x-ms-error-code": "TooManyRequests"}, \
                {"statusCode": 429, "message": f"Rate limit is exceeded. Try again in {retry_after} seconds."}
        self.windows[w] = used + 1
        ref = f"CPO-{zlib.crc32(po.encode()) % 900000 + 100000}"
        self.received.setdefault(po, clock)
        self.log.append(f"{ts(clock)} apim-contoso-parts POST /api/purchase-orders 201 {random.Random(po).randint(180, 420)}ms "
                        f"caller=power-platform remaining={self.LIMIT - used - 1} po={po} ref={ref}")
        return 201, {}, {"orderReference": ref, "status": "Received"}


def simulate(definition: dict):
    pos, _ = _events()
    api = ContosoPartsApi()
    results = []
    for i, po in enumerate(pos):
        run = run_flow(definition, api, po["t"], po)
        results.append((po, run, f"0858{6000000000 + i * 7919:011d}CU{i % 30:02d}"))
    return results, api


def write_incident(definition: dict, out: pathlib.Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "runs").mkdir(exist_ok=True)
    results, api = simulate(definition)
    _, others = _events()

    history = []
    for po, run, run_name in results:
        history.append({"name": run_name, "status": run.status, "startTime": ts(po["t"]),
                        "endTime": ts(max(r.end for r in run.records) if run.records else po["t"]),
                        "trigger": {"name": "When_a_PO_is_approved", "status": "Succeeded"},
                        "correlation": {"clientTrackingId": run_name}})
        failed = [r for r in run.records if r.status == "Failed"]
        if failed or run.status != "Succeeded":
            detail = {"name": run_name, "flow": FLOW_NAME, "status": run.status, "error": run.error,
                      "triggerOutputs": {"body/contoso_ponumber": po["contoso_ponumber"],
                                         "body/statuscode": po["statuscode"]},
                      "actions": []}
            for r in run.records:
                a = {"name": r.name, "scope": r.scope or None, "status": r.status,
                     "startTime": ts(r.start), "endTime": ts(r.end)}
                if r.attempts:
                    last = r.attempts[-1]
                    a["outputs"] = {"statusCode": last[1], "headers": last[2], "body": last[3]}
                    a["retryHistory"] = [{"startTime": ts(t), "code": str(c)} for t, c, _, _ in r.attempts[:-1]]
                if r.error:
                    a["error"] = {"code": r.error["code"], "message": json.dumps(r.error["body"])}
                if r.name == "Compose_failure_details":
                    a["outputs"] = {"body": "[ ...result('Try') array, truncated in this export... ]"}
                detail["actions"].append(a)
            (out / "runs" / f"{run_name}.json").write_text(json.dumps(detail, indent=2) + "\n")
    (out / "run-history.json").write_text(json.dumps({"flow": FLOW_NAME, "environment": "Contoso-PROD",
                                                       "value": history}, indent=2) + "\n")

    trig = [{"time": ts(po["t"]), "status": "Fired", "po": po["contoso_ponumber"]} for po, _, _ in results]
    trig += [{"time": ts(o["t"]), "status": "Skipped",
              "reason": "Trigger conditions not met: @equals(triggerOutputs()?['body/statuscode'], 100000003)",
              "po": o["contoso_ponumber"], "statuscode": o["statuscode"]} for o in others]
    trig.sort(key=lambda x: x["time"])
    (out / "trigger-history.json").write_text(json.dumps(trig, indent=2) + "\n")

    (out / "apim-gateway.log").write_text("\n".join(sorted(api.log)) + "\n")

    with open(out / "dataverse-approved-pos.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["contoso_ponumber", "statuscode", "approved_on", "contoso_partsreference", "contoso_syncstatus"])
        for po, run, _ in results:
            sent = po["contoso_ponumber"] in api.received
            w.writerow([po["contoso_ponumber"], "Approved", ts(po["t"]),
                        f"CPO-{zlib.crc32(po['contoso_ponumber'].encode()) % 900000 + 100000}" if sent else "",
                        "Sent" if sent else ("Failed" if run.status == "Failed" else "")])
    with open(out / "contoso-parts-received.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["po_number", "received_utc"])
        for po_num, t in sorted(api.received.items(), key=lambda x: x[1]):
            w.writerow([po_num, ts(t)])

    total = len(results)
    lost = [po["contoso_ponumber"] for po, run, _ in results
            if po["contoso_ponumber"] not in api.received and run.status == "Succeeded"]
    (out / "SUMMARY.txt").write_text(
        f"Incident bundle for {FLOW_NAME} on 2026-10-06 (generated by make setup)\n"
        f"Approved POs (flow runs): {total}\n"
        f"Runs Succeeded: {sum(1 for _, r, _ in results if r.status == 'Succeeded')}  "
        f"Failed: {sum(1 for _, r, _ in results if r.status == 'Failed')}\n"
        f"Received by Contoso Parts: {len(api.received)}\n"
        "Files: run-history.json, runs/<run>.json (runs with a failed action), trigger-history.json,\n"
        "       apim-gateway.log, dataverse-approved-pos.csv, contoso-parts-received.csv\n")
    return {"total": total, "lost": lost}


def outcome(definition: dict) -> dict:
    """Used by the tests: delivered / silently lost / loudly failed counts."""
    results, api = simulate(definition)
    delivered = sum(1 for po, _, _ in results if po["contoso_ponumber"] in api.received)
    silent = sum(1 for po, run, _ in results if po["contoso_ponumber"] not in api.received and run.status == "Succeeded")
    loud = sum(1 for po, run, _ in results if po["contoso_ponumber"] not in api.received and run.status == "Failed")
    return {"total": len(results), "delivered": delivered, "silently_lost": silent, "failed_runs": loud}

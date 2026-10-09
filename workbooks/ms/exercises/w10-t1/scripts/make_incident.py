"""Generate the incident bundle for ms/w10-t1 into ./incident.

The evidence is produced by replaying production traffic against the agent configuration that
was live in production (scripts/prod_snapshot = solution 1.8.0.0) through the same proxy
orchestrator the tests use, so the activity maps are consistent with the configuration.
"""
import csv
import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tests"))
from proxy_router import load_components, router_for  # noqa: E402

import yaml  # noqa: E402

OUT = ROOT / "incident"
SNAP = HERE / "prod_snapshot" / "agent"

PROD_UTTERANCES = [
    ("conv-7f3a1c", "2026-10-06T08:12:44Z", "how many vacation days do I have left?"),
    ("conv-7f3b02", "2026-10-06T08:40:10Z", "do I have any PTO left for December"),
    ("conv-7f3c9e", "2026-10-06T09:05:51Z", "how many sick days have I used this year"),
    ("conv-7f3d11", "2026-10-06T10:22:37Z", "book vacation Dec 22 to Dec 31"),
    ("conv-7f3e4b", "2026-10-06T11:47:02Z", "what's my leave balance"),
    ("conv-7f3f80", "2026-10-06T13:03:19Z", "how many days off do I still have"),
]

EVAL_SET = [
    ("how many PTO days do I have", "tool:GetPtoBalance"),
    ("remaining vacation balance", "tool:GetPtoBalance"),
    ("how many days of leave are left for me", "tool:GetPtoBalance"),
    ("I need to request vacation next week", "tool:SubmitLeaveRequest"),
    ("submit sick leave for today", "tool:SubmitLeaveRequest"),
    ("what holidays do we get in Canada", "topic:HolidayCalendar"),
    ("can I carry over unused vacation to next year", "knowledge:HRPolicyHandbook"),
    ("what is the parental leave policy", "knowledge:HRPolicyHandbook"),
]


def tool_meta(key):
    kind, name = key.split(":", 1)
    if kind != "tool":
        return None
    return yaml.safe_load((SNAP / "tools" / f"{name}.tool.yaml").read_text())


def main():
    router = router_for(SNAP)
    names = {c.key: c.name for c in load_components(SNAP)}
    (OUT / "activity-map").mkdir(parents=True, exist_ok=True)
    (OUT / "analytics").mkdir(parents=True, exist_ok=True)
    (OUT / "evaluation").mkdir(parents=True, exist_ok=True)
    (OUT / "knowledge").mkdir(parents=True, exist_ok=True)

    (OUT / "PAGER.txt").write_text(
        "Ticket HRIT-5531  Sev 3  opened 2026-10-07 09:14 by HR Operations\n"
        "Title: HR Assist keeps trying to book leave when people ask about their balance\n\n"
        "Since last Thursday, employees who ask HR Assist in Teams how many vacation days they\n"
        "have left are asked 'What is the first day of your leave?' and then 'How many hours...'.\n"
        "Most give up. HR inbox volume for balance questions is up 3x. Two people say the agent\n"
        "'almost booked a holiday' for them. Nothing was changed on our side except adding the new\n"
        "leave request feature. Please fix before payroll cut-off on Friday.\n"
    )

    for conv, ts, text in PROD_UTTERANCES:
        ranked = router.scores(text)
        chosen = ranked[0][0]
        meta = tool_meta(chosen)
        steps = [{"step": 1, "type": chosen.split(":")[0], "component": names[chosen],
                  "componentId": chosen, "status": "started"}]
        generated = []
        filled = {}
        if meta:
            for inp in meta.get("inputs") or []:
                if inp.get("shouldPromptUser"):
                    generated.append(f"(generated question for input '{inp['propertyName']}')")
                else:
                    filled[inp["propertyName"]] = None
            if chosen.endswith("SubmitLeaveRequest"):
                generated = ["What type of leave would you like?",
                             "What is the first day of your leave?",
                             "What is the last day of your leave?",
                             "How many hours of leave per day?"]
                filled = {"leaveType": "vacation" if "vacation" in text or "PTO" in text else None,
                          "startDate": None, "endDate": None, "hours": None}
            if chosen.endswith("GetPtoBalance"):
                filled = {"employeeId": None}
                generated = ["What is your employee ID?"]
        outcome = "abandoned" if chosen.endswith("SubmitLeaveRequest") and "book" not in text else "completed"
        doc = {
            "conversationId": conv,
            "timestamp": ts,
            "channel": "msteams",
            "userMessage": text,
            "plan": steps,
            "candidatesConsidered": [{"componentId": k, "name": names[k]} for k, _ in ranked[:3]],
            "inputsFilledFromContext": filled,
            "questionsGeneratedByOrchestrator": generated,
            "outcome": outcome,
            "note": "Reconstructed from the test pane activity map and the conversation transcript.",
        }
        (OUT / "activity-map" / f"{conv}.json").write_text(json.dumps(doc, indent=2) + "\n")

    with (OUT / "analytics" / "tool-usage-2026-W41.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["component", "type", "invocations", "completed", "abandoned_after_first_question", "avg_turns"])
        w.writerow(["Leave and PTO", "tool", 1874, 211, 1502, 3.8])
        w.writerow(["Get PTO balance", "tool", 37, 35, 2, 1.4])
        w.writerow(["Holiday calendar", "topic", 402, 398, 0, 1.1])
        w.writerow(["HR policy handbook", "knowledge", 655, 611, 0, 1.2])
        w.writerow(["Facilities site", "knowledge", 58, 51, 0, 1.3])

    with (OUT / "analytics" / "session-outcomes-2026-W40-W41.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["week", "sessions", "resolved", "escalated", "abandoned", "csat_avg"])
        w.writerow(["2026-W40", 3120, 2496, 312, 312, 4.1])
        w.writerow(["2026-W41", 3388, 1694, 340, 1354, 2.6])

    with (OUT / "evaluation" / "test-set-run-2026-10-06.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["utterance", "expected", "actual", "result"])
        for u, exp in EVAL_SET:
            got = router.route(u)
            w.writerow([u, exp, got, "pass" if got == exp else "FAIL"])

    rng = random.Random(41)
    lines = []
    for day in range(1, 8):
        lines.append(f"2026-10-0{day}T02:00:{rng.randint(10, 59)}Z INFO  knowledge=HR policy handbook source=https://litware.sharepoint.com/sites/HR/Policies indexed=48 skipped=0 status=Ready")
        lines.append(f"2026-10-0{day}T02:01:{rng.randint(10, 59)}Z WARN  knowledge=Facilities site source=https://litware.sharepoint.com/sites/Facilities indexed=212 skipped=3 reason=FileTooLarge files=[Campus-Map-2026.pdf, Fire-Evacuation-Plan-B4.pdf, Parking-Allocation.xlsx] status=Ready")
    (OUT / "knowledge" / "indexing-status.log").write_text("\n".join(lines) + "\n")

    (OUT / "solution-history.csv").write_text(
        "version,imported_on,imported_by,notes\n"
        "1.6.0.0,2026-09-08,pipeline:hr-agents-prod,Holiday calendar topic\n"
        "1.7.0.0,2026-09-22,pipeline:hr-agents-prod,Added Facilities site knowledge source\n"
        "1.8.0.0,2026-10-02,pipeline:hr-agents-prod,Added leave submission tool (Workday SubmitTimeOffRequest)\n"
    )
    print(f"incident bundle written to {OUT}")


if __name__ == "__main__":
    main()

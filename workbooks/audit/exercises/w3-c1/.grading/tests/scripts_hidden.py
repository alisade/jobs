"""Model scripts shared by the tests."""

import json

from tester.scripted import call, say


def happy():
    s = [call("list_sample")]
    rows = []
    for cid, pr, res, failed in (("CHG-104118", 2231, "pass", []), ("CHG-104163", 2240, "pass", []),
                                 ("CHG-104390", 2302, "exception", ["independent_approver"])):
        s += [call("get_ticket", change_id=cid), call("get_pr", pr_number=pr), call("get_deploy_record", change_id=cid),
              call("record_result", change_id=cid, result=res, failed_attributes=failed, citations=[f"ticket:{cid}"])]
        rows.append({"change_id": cid, "result": res, "failed_attributes": failed})
    s.append(say(json.dumps({"control": "CM-03", "results": rows})))
    return s, rows

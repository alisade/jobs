from lighthouse.bedrock_stub import FakeConverse, cost_usd
from lighthouse.builder import build_request

TOOLS = ["get_ticket", "create_ticket", "list_pending_reviews", "get_change", "add_comment"]


class Clock:
    def __init__(self, t=1794830400.0):
        self.t = t

    def __call__(self):
        return self.t


def send(client, req):
    return client.converse(req["modelId"], req["messages"], system=req["system"], toolConfig=req["toolConfig"],
                           inferenceConfig=req["inferenceConfig"])["usage"]


def conversation(client, clock, user, n_turns=3, tools=TOOLS, start_id=0):
    usages = []
    for i in range(n_turns):
        req = build_request(user, f"question {i} from {user}", f"req-{start_id + i:06d}", clock(), tools)
        usages.append(send(client, req))
        clock.t += 20
    return usages


def total_cost(usages):
    return sum(cost_usd(u) for u in usages)

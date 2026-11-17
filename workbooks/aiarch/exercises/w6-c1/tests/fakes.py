from pathlib import Path

from ssmsim import FakeAws, run

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = "lighthouse_helpdesk_prod-Q2w3E4r5T6"
PARAMS = {"AutomationAssumeRole": "arn:aws:iam::111100000004:role/lighthouse-ssm-rollback",
          "AgentRuntimeId": RUNTIME, "TargetVersion": "7", "BackupBucket": "hpm-lighthouse-prod-backups"}


class World:
    def __init__(self, live="9", ready_after=2, errors=1, never_ready=False):
        self.live, self.status, self.polls = live, "READY", 0
        self.ready_after, self.never_ready = ready_after, never_ready
        self.objects = {}
        self.aws = FakeAws()
        self.aws.register("bedrock-agentcore-control", "GetAgentRuntimeEndpoint", self.get)
        self.aws.register("bedrock-agentcore-control", "UpdateAgentRuntimeEndpoint", self.update)
        self.aws.register("s3", "PutObject", self.put)
        self.aws.register("cloudwatch", "GetMetricStatistics", lambda p: {"Datapoints": [{"Sum": float(errors)}]})

    def get(self, p):
        if self.status == "UPDATING":
            self.polls += 1
            if self.polls >= self.ready_after and not self.never_ready:
                self.status = "READY"
        return {"name": p["endpointName"], "liveVersion": self.live, "status": self.status}

    def update(self, p):
        self.live, self.status, self.polls = p["agentRuntimeVersion"], "UPDATING", 0
        return {"status": "UPDATING"}

    def put(self, p):
        self.objects[p["Key"]] = p["Body"]
        return {"ETag": "x"}

    def apis(self):
        return [a for _, a, _ in self.aws.calls]


def execute(world, approve=lambda i: True, **overrides):
    text = (ROOT / "runbooks/rollback-agent-endpoint.yaml").read_text()
    return run(text, {**PARAMS, **overrides}, world.aws, approve=approve)

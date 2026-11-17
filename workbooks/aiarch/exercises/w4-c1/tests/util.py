import time

from obo.fakeidp import ISSUER, FakeIdP

TARGETS = {"access-requests": {"audience": "https://access.harborpoint.example",
                               "resource": "https://access.harborpoint.example/api",
                               "scopes": ["access.request.read", "access.request.write"]}}


class Clock:
    def __init__(self):
        self.t = time.time()

    def __call__(self):
        return self.t


def make(actor=True, faults=()):
    from obo.exchange import OboClient
    clock = Clock()
    idp = FakeIdP(clock=clock)
    idp.faults = set(faults)
    client = OboClient(idp.token_endpoint, idp.jwks(), ISSUER, TARGETS, clock=clock,
                       actor_token=(lambda: idp.agent_token()) if actor else None,
                       agent_client_id="lighthouse-agent" if actor else None)
    return idp, client, clock

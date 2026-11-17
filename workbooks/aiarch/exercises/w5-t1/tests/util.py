from lighthouse import agent, telemetry

CALLS = [{"id": "t1", "name": "get_change", "args": {"change_id": "CHG-9001"}},
         {"id": "t2", "name": "get_change", "args": {"change_id": "CHG-9002"}},
         {"id": "t3", "name": "get_change", "args": {"change_id": "CHG-9999"}}]


def run(calls):
    exp = telemetry.setup()
    out = agent.run_turn("sess-1", calls)
    return out, exp.get_finished_spans()


def by_name(spans, prefix):
    return [s for s in spans if s.name.startswith(prefix)]

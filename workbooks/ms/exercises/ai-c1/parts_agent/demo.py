"""Replay a recorded conversation fixture through your loop and print what happened. Provided.
Usage: python -m parts_agent.demo fixtures/injection.json"""
import json
import sys

from parts_agent.backend import Backend
from parts_agent.fake_model import FakeModelClient
from parts_agent.loop import run_turn
from parts_agent.session import Session


def main(path: str) -> int:
    fx = json.load(open(path))
    client = FakeModelClient(fx["turns"])
    session = Session(backend=Backend())
    for i, text in enumerate(fx["user_turns"]):
        for qid in fx.get("confirm_before_turn", {}).get(str(i), []):
            session.confirm(qid)
            print(f"[app] technician confirmed {qid}")
        print(f"[user] {text}")
        res = run_turn(client, session, text)
        for call in res.tool_calls:
            flag = "ERROR" if call["is_error"] else "ok"
            print(f"  [tool] {call['name']} {json.dumps(call['input'])} -> {flag}")
        print(f"[agent:{res.stop_reason}] {res.final_text}")
        print(f"  usage {res.usage}, model calls {res.model_calls}")
    print(f"[backend] orders placed: {session.backend.orders}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

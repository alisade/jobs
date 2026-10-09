"""Visible tests: structure plus one happy-path conversation. Hidden tests go further."""
import pathlib

import pytest
import yaml

from topicsim import RESET_FLOW, new_session

AGENT = pathlib.Path(__file__).resolve().parent.parent / "agent"
TRIGGERS = {
    "ConversationStart": "OnConversationStart",
    "ResetPassword": "OnRecognizedIntent",
    "Fallback": "OnUnknownIntent",
    "Escalate": "OnEscalate",
}


@pytest.mark.parametrize("name,trigger", TRIGGERS.items())
def test_topic_parses_with_expected_trigger(name, trigger):
    doc = yaml.safe_load((AGENT / "topics" / f"{name}.topic.yaml").read_text())
    assert doc["kind"] == "AdaptiveDialog"
    assert doc["beginDialog"]["kind"] == trigger


def test_reset_password_happy_path():
    s = new_session(AGENT)
    s.recognized("ResetPassword", "I'm locked out of VPN", answers=[True, "VPN"])
    calls = [c for c in s.flow_calls if c[0] == RESET_FLOW]
    assert len(calls) == 1
    assert calls[0][1] == {"upn": "dana.kim@litware.com", "system": "VPN"}
    assert "VPN" in s.transcript[-1]


def test_first_unrecognized_message_asks_to_rephrase():
    s = new_session(AGENT)
    s.unrecognized("blorp")
    assert "rephrase" in s.transcript[-1].lower()
    assert s.flow_calls == []

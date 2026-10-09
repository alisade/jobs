"""Hidden tests for ms/w9-c1: static validation of the topic YAML plus scripted conversations."""
import pathlib
import re

import pytest
import yaml

from topicsim_hidden import RESET_FLOW, TICKET_FLOW, SimError, load_topics, new_session

AGENT = pathlib.Path(__file__).resolve().parent.parent.parent / "agent"
TOPICS = load_topics(AGENT)
FLOW_INPUTS = {RESET_FLOW: {"upn", "system"}, TICKET_FLOW: {"upn", "reason", "summary"}}
VAR_RE = re.compile(r"\b(Topic|Global)\.([A-Za-z_][A-Za-z0-9_]*)")


def walk(actions):
    """Yield every node in document order, descending into branches."""
    for node in actions or []:
        yield node
        if node.get("kind") == "ConditionGroup":
            for c in node.get("conditions") or []:
                yield {"kind": "_Condition", "condition": c.get("condition"), "id": c.get("id")}
                yield from walk(c.get("actions"))
            yield from walk(node.get("elseActions"))


def reads(node):
    texts = []
    k = node.get("kind")
    if k == "_Condition":
        texts.append(str(node.get("condition")))
    elif k == "SetVariable" and isinstance(node.get("value"), str) and node["value"].startswith("="):
        texts.append(node["value"])
    elif k == "SendActivity":
        texts.append(str(node.get("activity")))
    elif k == "InvokeFlowAction":
        texts += [str(v) for v in (((node.get("input") or {}).get("binding")) or {}).values()]
    return [(m.group(1), m.group(2)) for t in texts for m in VAR_RE.finditer(t)]


def writes(node):
    k = node.get("kind")
    out = []
    if k in ("SetVariable", "Question"):
        out.append(str(node.get("variable", "")).replace("init:", ""))
    if k == "InvokeFlowAction":
        out += [str(v) for v in (((node.get("output") or {}).get("binding")) or {}).values()]
    return [tuple(v.split(".", 1)) for v in out if "." in v]


def all_nodes(doc):
    return list(walk(doc["beginDialog"].get("actions")))


# ------------------------------------------------------------------ static checks

def test_all_four_topics_present():
    assert set(TOPICS) >= {"ConversationStart", "ResetPassword", "Fallback", "Escalate"}


def test_node_ids_unique_within_each_topic():
    for name in TOPICS:
        ids = [n.get("id") for n in all_nodes(TOPICS[name])]
        assert all(ids), f"{name}: every node and condition needs an id"
        assert len(ids) == len(set(ids)), f"{name}: duplicate ids {sorted(i for i in ids if ids.count(i) > 1)}"


def test_topic_variables_set_before_read():
    for name in TOPICS:
        seen = set()
        for node in all_nodes(TOPICS[name]):
            for scope, var in reads(node):
                if scope == "Topic":
                    assert var in seen, f"{name}: Topic.{var} is read before any node sets it"
            for scope, var in writes(node):
                if scope == "Topic":
                    seen.add(var)


def test_global_variables_are_initialized_somewhere():
    written = {v for d in TOPICS.values() for n in all_nodes(d) for s, v in writes(n) if s == "Global"}
    read = {v for d in TOPICS.values() for n in all_nodes(d) for s, v in reads(n) if s == "Global"}
    assert read <= written, f"Global variables read but never set: {sorted(read - written)}"


def test_every_question_is_complete():
    for name, d in TOPICS.items():
        for n in all_nodes(d):
            if n.get("kind") == "Question":
                assert n.get("entity"), f"{name}/{n.get('id')}: Question without entity"
                assert n.get("prompt"), f"{name}/{n.get('id')}: Question without prompt"
                assert str(n.get("variable", "")).startswith(("init:Topic.", "Topic.")), f"{name}/{n.get('id')}: Question must store into a Topic variable"


def test_flow_calls_match_contract():
    found = set()
    for name, d in TOPICS.items():
        for n in all_nodes(d):
            if n.get("kind") == "InvokeFlowAction":
                fid = n.get("flowId")
                assert fid in FLOW_INPUTS, f"{name}: unknown flowId {fid}"
                got = set(((n.get("input") or {}).get("binding")) or {})
                assert got == FLOW_INPUTS[fid], f"{name}: flow {fid} inputs {sorted(got)} != contract {sorted(FLOW_INPUTS[fid])}"
                found.add(fid)
    assert found == set(FLOW_INPUTS)


def test_reset_password_model_description_is_useful():
    d = TOPICS["ResetPassword"]
    desc = str(d.get("modelDescription", ""))
    assert len(desc) >= 120, "modelDescription is what generative orchestration reads; make it specific"
    assert "password" in desc.lower()
    assert re.search(r"\b(do not|don't|not for|never|doesn't)\b", desc, re.I), "say what the topic does NOT handle"
    tq = d["beginDialog"]["intent"]["triggerQueries"]
    assert len(set(tq)) >= 5


def test_fallback_uses_system_fallback_count():
    text = yaml.safe_dump(TOPICS["Fallback"])
    assert "System.FallbackCount" in text


def test_escalate_has_trigger_queries():
    d = TOPICS["Escalate"]
    assert len(d["beginDialog"]["intent"]["triggerQueries"]) >= 3


# ------------------------------------------------------------------ conversations

def tickets(s):
    return [c[1] for c in s.flow_calls if c[0] == TICKET_FLOW]


def test_reset_success_has_no_ticket():
    s = new_session(AGENT)
    s.recognized("ResetPassword", "forgot my SAP password", answers=[True, "SAP"])
    assert tickets(s) == []
    assert "SAP" in s.transcript[-1]
    assert s.questions_asked == ["question_ownAccount", "question_system"] or len(s.questions_asked) == 2


def test_someone_elses_account_never_reaches_the_flow():
    s = new_session(AGENT)
    s.recognized("ResetPassword", "reset my colleague's password", answers=[False])
    assert s.flow_calls == []
    assert "manager" in s.transcript[-1].lower()
    assert len(s.questions_asked) == 1


def test_reset_failure_escalates_with_reason():
    s = new_session(AGENT, reset_status="Failed")
    s.recognized("ResetPassword", "locked out of windows", answers=[True, "Windows sign-in"])
    t = tickets(s)
    assert len(t) == 1
    assert t[0]["reason"] == "PasswordResetFailed"
    assert t[0]["upn"] == "dana.kim@litware.com"
    assert "INC0042117" in s.transcript[-1]


def test_escalation_reason_is_cleared_after_ticket():
    s = new_session(AGENT, reset_status="Failed")
    s.recognized("ResetPassword", "locked out", answers=[True, "VPN"])
    assert s.globals.get("EscalationReason") in (None, "")


def test_direct_escalation_defaults_to_user_requested():
    s = new_session(AGENT)
    s.escalate("talk to a person please")
    t = tickets(s)
    assert len(t) == 1
    assert t[0]["reason"] == "UserRequested"
    assert t[0]["summary"] == "talk to a person please"


def test_second_escalation_is_not_mislabelled():
    s = new_session(AGENT, reset_status="Failed")
    s.recognized("ResetPassword", "locked out", answers=[True, "VPN"])
    s.escalate("still need a human")
    t = tickets(s)
    assert [x["reason"] for x in t] == ["PasswordResetFailed", "UserRequested"]
    assert "INC0042118" in s.transcript[-1]


def test_two_misses_rephrase_third_escalates():
    s = new_session(AGENT)
    s.unrecognized("blorp")
    s.unrecognized("zzz")
    assert tickets(s) == []
    assert all("rephrase" in m.lower() for m in s.transcript[-2:])
    s.unrecognized("printer on fire")
    t = tickets(s)
    assert len(t) == 1
    assert t[0]["reason"] == "Unrecognized"
    assert t[0]["summary"] == "printer on fire"


def test_recognized_topic_resets_the_fallback_count():
    s = new_session(AGENT)
    s.unrecognized("blorp")
    s.unrecognized("zzz")
    s.recognized("ResetPassword", "reset my password", answers=[True, "VPN"])
    s.unrecognized("hmm")
    assert tickets(s) == []
    assert "rephrase" in s.transcript[-1].lower()


def test_simulator_rejects_unknown_node_kinds():
    # Guard: the agent must only use node kinds the README lists, so the conversations above are meaningful.
    allowed = {"SendActivity", "Question", "ConditionGroup", "SetVariable", "BeginDialog",
               "InvokeFlowAction", "EndDialog", "EndConversation", "CancelAllDialogs", "_Condition"}
    used = {n.get("kind") for d in TOPICS.values() for n in all_nodes(d)}
    assert used <= allowed, f"unsupported node kinds: {sorted(used - allowed)}"

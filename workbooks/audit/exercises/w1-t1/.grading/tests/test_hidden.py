"""Hidden tests for audit/w1-t1."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from controlpilot import data, pipeline
from controlpilot.fake_gemini import FakeClient

EXPECTED = {"S07": {"approval_before_deploy"}, "S12": {"independent_approver"},
            "S18": {"approval_before_deploy", "independent_approver"}, "S21": {"approval_before_deploy"}}


@pytest.fixture(scope="module")
def results():
    client = FakeClient()
    out = {r.sample_id: r for r in pipeline.run(client, data.samples(), data.deploys(), data.directory())}
    return out, client


def test_exactly_the_four_exceptions(results):
    res, _ = results
    assert {k for k, r in res.items() if r.result == "exception"} == set(EXPECTED)


@pytest.mark.parametrize("sid", sorted(EXPECTED))
def test_exception_reasons(results, sid):
    res, _ = results
    assert set(res[sid].failed) >= EXPECTED[sid]


def test_other_samples_still_pass(results):
    res, _ = results
    assert sum(1 for k, r in res.items() if k not in EXPECTED and r.result == "pass") == 21


def test_request_uses_a_response_schema(results):
    _, client = results
    cfg = client.models.requests[0]["config"]
    assert (getattr(cfg, "response_schema", None) or getattr(cfg, "response_json_schema", None)) is not None


def _contract():
    from controlpilot import contract
    for name in ("ChangeFacts", "ChangeEvidence", "ChangeAssessment"):
        if hasattr(contract, name):
            cls = getattr(contract, name)
            cfg = getattr(pipeline.build_config(), "response_schema", None)
            if cfg is not None and isinstance(cfg, type):
                return cfg
            return cls
    raise AssertionError("no contract class found")


def _good():
    return json.loads(FakeClient().models.constrained["CHG-104903"])


def test_contract_rejects_missing_key():
    cls = _contract()
    d = _good()
    d.pop("approver")
    with pytest.raises(ValidationError):
        cls.model_validate(d)


def test_contract_rejects_unknown_key():
    cls = _contract()
    d = _good()
    d["approval_precedes_deploy"] = True
    with pytest.raises(ValidationError):
        cls.model_validate(d)


def test_freeform_v2_response_never_becomes_a_pass():
    """If someone drops the schema again, the renamed keys must not silently pass."""
    class NoSchemaModels:
        def __init__(self):
            self.inner = FakeClient().models

        def generate_content(self, *, model, contents, config=None):
            config = config.model_copy(update={"response_schema": None, "response_json_schema": None})
            return self.inner.generate_content(model=model, contents=contents, config=config)

    class C:
        models = NoSchemaModels()

    s = data.samples()["S07"]
    r = pipeline.test_sample(C(), s, data.deploys()[s["change_id"]], data.directory())
    assert r.result in ("needs_review", "exception")


def test_time_zone_case_is_decided_by_timestamps(results):
    """S21: the freeform model said true; 09:10+02:00 is 07:10Z, after the 06:30Z deploy."""
    res, _ = results
    assert res["S21"].result == "exception"

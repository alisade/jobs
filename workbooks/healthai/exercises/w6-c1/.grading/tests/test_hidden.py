"""Hidden tests for healthai/w6-c1: planted identifiers never reach logs, prompts or spans."""

import json

import pytest

from deid.core import (age_band, build_prompt, minimum_necessary, names_from_patient, pseudonymize_member_id,
                       redact_obj, redact_text, scrub_span_attributes)

NAMES = ["Rosalind", "June", "Okafor-Benn"]
LEAKS = ["rosalind", "okafor", "benn", "june", "m-100417", "8812044", "123-45-6789", "201-7788", "201.7790",
         "201 7791", "example.org", "larchmont", "44122", "1934", "02/11", "march 14", "14 mar", "2026-03-14"]
PLANTED = ("ROSALIND okafor-benn (M-100417, MRN 8812044, SSN 123-45-6789) phones (555) 201-7788, 555.201.7790, "
           "+1 555 201 7791, mail r.okaforbenn@example.org, 4417 Larchmont Avenue, Fairhaven OH 44122, "
           "DOB 02/11/1934, seen March 14, 2026, 14 Mar 2026 and 2026-03-14; June visited.")


def leaked(text):
    low = text.lower()
    return [x for x in LEAKS if x in low]


def test_planted_free_text_is_clean():
    assert leaked(redact_text(PLANTED, NAMES)) == []


@pytest.mark.parametrize("snippet,expect_gone", [
    ("call 555-201-7788 today", "201-7788"),
    ("call (555)201-7788 today", "201-7788"),
    ("DOB: 2/11/34", "2/11/34"),
    ("born February 11th, 1934", "february 11"),
    ("ZIP 44122 on file", "44122"),
    ("lives at 12 Old Mill Road", "old mill"),
    ("MRN# A77-1203", "a77-1203"),
    ("SSN: 123456789", "123456789"),
])
def test_formats(snippet, expect_gone):
    assert expect_gone not in redact_text(snippet, NAMES).lower()


@pytest.mark.parametrize("snippet", ["92-year-old female", "age 93", "a 95 yo man", "Age: 101"])
def test_ages_over_89(snippet):
    out = redact_text(snippet, NAMES)
    assert not any(n in out for n in ("92", "93", "95", "101")), out


def test_clinical_content_is_preserved():
    text = "Dx M54.16 and M51.26, naproxen 500 mg, step therapy 6 weeks, pain 7/10, policy KHP-MP-0417 2.b, age 45"
    out = redact_text(text, NAMES)
    for keep in ["M54.16", "M51.26", "500 mg", "6 weeks", "7/10", "KHP-MP-0417 2.b", "age 45"]:
        assert keep in out, keep


def test_pseudonym_is_keyed_and_deterministic():
    a = pseudonymize_member_id("M-100417", b"k1")
    assert a == pseudonymize_member_id("M-100417", b"k1")
    assert a != pseudonymize_member_id("M-100417", b"k2")
    assert a != pseudonymize_member_id("M-100418", b"k1")
    assert "100417" not in a
    assert redact_text("member M-100417", NAMES, b"k1") == f"member {a}"


def test_names_from_patient(bundle):
    p = bundle["entry"][0]["resource"]
    assert {"Rosalind", "June", "Okafor-Benn"} <= set(names_from_patient(p))


def test_redact_obj_nested_and_identifier_keys():
    obj = {"case": "PA-1", "patient": {"name": [{"family": "Okafor-Benn"}], "birthDate": "1934-02-11"},
           "notes": ["Rosalind called from (555) 201-7788", {"deep": {"text": "SSN 123-45-6789"}}],
           "code": "M54.16"}
    out = redact_obj(obj, NAMES)
    assert leaked(json.dumps(out)) == []
    assert out["code"] == "M54.16" and out["case"] == "PA-1"


def test_age_band():
    assert age_band("1934-02-11") == "90+"
    assert age_band("1981-06-01") == "40-49"
    assert age_band("2016-01-01") == "10-19"


def test_minimum_necessary_fields_only(bundle):
    ctx = minimum_necessary(bundle)
    assert set(ctx) == {"member_token", "age_band", "sex", "conditions", "medications", "observations", "service", "notes"}
    assert ctx["conditions"] == ["M54.16", "M51.26"] and ctx["service"] == "lumbar-mri"
    assert ctx["age_band"] == "90+" and ctx["member_token"].startswith("MBR-")
    assert leaked(json.dumps(ctx)) == []
    assert "8 weeks of physical therapy" in ctx["notes"][0]


def test_prompt_clean(bundle):
    assert leaked(build_prompt(bundle, "policy text")) == []


def test_log_args_are_redacted(capture):
    capture.logger.info("prompt for %s (%s)", "Rosalind Okafor-Benn", "M-100417", extra={"case_note": "-"})
    assert leaked(capture.text()) == []


def test_log_extra_is_redacted(capture):
    capture.logger.info("note attached", extra={"case_note": "Rosalind called (555) 201-7788"})
    assert leaked(capture.text()) == []


def test_log_fstring_and_exception_are_redacted(capture):
    name = "Rosalind Okafor-Benn"
    try:
        raise ValueError(f"no coverage for {name} M-100417")
    except ValueError:
        capture.logger.exception(f"lookup failed for {name}", extra={"case_note": "-"})
    assert leaked(capture.text()) == []
    assert "ValueError" in capture.text()


def test_span_attributes_scrubbed():
    attrs = {"gen_ai.prompt": PLANTED, "khp.member_id": "M-100417", "khp.case_id": "PA-2026-0002",
             "gen_ai.usage.input_tokens": 812, "khp.context": {"note": "Rosalind called"}}
    out = scrub_span_attributes(attrs, NAMES)
    assert leaked(json.dumps(out)) == []
    assert out["khp.case_id"] == "PA-2026-0002" and out["gen_ai.usage.input_tokens"] == 812

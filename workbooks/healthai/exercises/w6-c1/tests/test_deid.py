from deid.core import build_prompt, redact_text

NAMES = ["Rosalind", "June", "Okafor-Benn"]


def test_ssn_and_email():
    out = redact_text("SSN 123-45-6789, mail r.ob@example.org", NAMES)
    assert "123-45-6789" not in out and "example.org" not in out


def test_names_and_member_id_redacted():
    out = redact_text("Rosalind Okafor-Benn (M-100417) called", NAMES)
    assert "Rosalind" not in out and "Okafor" not in out and "M-100417" not in out


def test_prompt_has_no_identifiers(bundle):
    p = build_prompt(bundle, "KHP-MP-0417 2.b: six weeks of conservative therapy")
    for leak in ["Rosalind", "Okafor", "M-100417", "MRN-8812044", "201-7788", "Larchmont", "1934-02-11", "44122"]:
        assert leak not in p, leak
    assert "M54.16" in p

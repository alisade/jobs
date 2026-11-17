"""De-identification for everything that leaves the PHI boundary: logs, prompts, trace attributes.

First draft from the platform team. It is not good enough to export traces or eval data (README).
Keep the public API: pseudonymize_member_id, names_from_patient, redact_text, redact_obj, age_band,
minimum_necessary, build_prompt, RedactingFilter, scrub_span_attributes.
"""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from .settings import AS_OF_YEAR, DEID_KEY  # noqa: F401

SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def pseudonymize_member_id(member_id: str, key: bytes = DEID_KEY) -> str:
    # TODO: keyed (HMAC-SHA256); a plain hash of a 6-digit id is reversible by brute force
    return "MBR-" + hashlib.sha256(member_id.encode()).hexdigest()[:12]


def names_from_patient(patient: dict) -> list[str]:
    return [n.get("family", "") for n in patient.get("name", [])]  # TODO: given names too


def redact_text(text: str, known_names=(), key: bytes = DEID_KEY) -> str:
    # TODO: names, member ids, MRN, phones, dates, addresses, ZIP, ages over 89 (README)
    text = SSN.sub("[SSN]", text)
    return EMAIL.sub("[EMAIL]", text)


def redact_obj(obj: Any, known_names=(), key: bytes = DEID_KEY) -> Any:
    if isinstance(obj, str):
        return redact_text(obj, known_names, key)
    return obj  # TODO: dicts and lists, identifier keys


def age_band(birth_date: str, as_of_year: int = AS_OF_YEAR) -> str:
    raise NotImplementedError  # TODO


def minimum_necessary(bundle: dict, key: bytes = DEID_KEY) -> dict:
    # TODO: only what the criteria step needs (README); today it forwards the whole Patient
    patient = [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient"][0]
    return {"patient": patient, "bundle_entries": len(bundle["entry"])}


def build_prompt(bundle: dict, policy_text: str, key: bytes = DEID_KEY) -> str:
    ctx = minimum_necessary(bundle, key)
    lines = ["Check the request against the policy. Recommend only.", f"POLICY: {policy_text}"]
    lines += [f"{k.upper()}: {v}" for k, v in ctx.items()]
    return "\n".join(lines)


class RedactingFilter(logging.Filter):
    def __init__(self, known_names=(), key: bytes = DEID_KEY):
        super().__init__()
        self.known_names = list(known_names)
        self.key = key

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_text(str(record.msg), self.known_names, self.key)  # TODO: args, exceptions, extra
        return True


def scrub_span_attributes(attrs: dict, known_names=(), key: bytes = DEID_KEY) -> dict:
    return dict(attrs)  # TODO

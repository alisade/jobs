"""De-identification for everything that leaves the PHI boundary: logs, prompts, trace attributes."""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
from datetime import date
from typing import Any

from .settings import AS_OF_YEAR, DEID_KEY

MONTHS = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[EMAIL]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (re.compile(r"\b(?:SSN|social security(?: number)?)\s*[:#]?\s*\d{9}\b", re.I), "[SSN]"),
    (re.compile(r"\bMRN[-:#\s]*[A-Z0-9-]*\d[A-Z0-9-]*\b", re.I), "[MRN]"),
    (re.compile(r"(?:\+?1[\s.-]?)?(?:\(\d{3}\)\s?|\b\d{3}[\s.-])\d{3}[\s.-]\d{4}\b"), "[PHONE]"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}(?:T[\d:.]+(?:Z|[+-]\d{2}:?\d{2})?)?\b"), "[DATE]"),
    (re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"), "[DATE]"),
    (re.compile(rf"\b{MONTHS}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b", re.I), "[DATE]"),
    (re.compile(rf"\b\d{{1,2}}\s+{MONTHS}\.?,?\s+\d{{4}}\b", re.I), "[DATE]"),
    (re.compile(r"\b\d{1,6}\s+(?:[A-Z][a-z]+\s+){1,3}(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd|Court|Ct|Way)\b\.?"), "[ADDRESS]"),
    (re.compile(r"\b\d{5}-\d{4}\b"), "[ZIP]"),
    (re.compile(r"(?<=\b[A-Z]{2}\s)\d{5}\b"), "[ZIP]"),
    (re.compile(r"\b(?:ZIP|postal code)\s*[:#]?\s*\d{5}\b", re.I), "[ZIP]"),
]
AGE = re.compile(r"\b(\d{2,3})(\s*-?\s*(?:years?|yrs?|y/?o)\b(?:-old)?|(?=\s*-year-old))", re.I)
AGE_WORD = re.compile(r"\bage[d]?\s*[:#]?\s*(\d{2,3})\b", re.I)
MEMBER = re.compile(r"\bM-\d{6}\b")
ID_KEYS = {"name", "given", "family", "birthdate", "telecom", "address", "identifier", "ssn", "mrn",
           "member_id", "memberid", "subscriberid", "phone", "email", "postalcode", "line"}


def pseudonymize_member_id(member_id: str, key: bytes = DEID_KEY) -> str:
    digest = hmac.new(key, member_id.encode(), hashlib.sha256).hexdigest()
    return f"MBR-{digest[:12]}"


def names_from_patient(patient: dict) -> list[str]:
    out: list[str] = []
    for n in patient.get("name", []):
        parts = list(n.get("given", [])) + ([n["family"]] if n.get("family") else [])
        out.extend(parts)
        if n.get("text"):
            out.append(n["text"])
    out = sorted({p for p in out if p and len(p) > 1}, key=len, reverse=True)
    return out


def _ages(text: str) -> str:
    """Safe Harbor: ages over 89 are aggregated into 90+."""
    text = AGE.sub(lambda m: "[AGE-OVER-89]" if int(m.group(1)) >= 90 else m.group(0), text)
    return AGE_WORD.sub(lambda m: "age [AGE-OVER-89]" if int(m.group(1)) >= 90 else m.group(0), text)


def redact_text(text: str, known_names: list[str] | tuple[str, ...] = (), key: bytes = DEID_KEY) -> str:
    if not isinstance(text, str):
        text = str(text)
    for name in sorted(known_names, key=len, reverse=True):
        for part in [name] + name.split("-"):
            if len(part) > 1:
                text = re.sub(rf"(?<![\w]){re.escape(part)}(?![\w])", "[NAME]", text, flags=re.I)
    text = MEMBER.sub(lambda m: pseudonymize_member_id(m.group(0), key), text)
    for pat, repl in PATTERNS:
        text = pat.sub(repl, text)
    text = re.sub(r"\[NAME\](?:-\[NAME\])+", "[NAME]", text)
    return _ages(text)


def redact_obj(obj: Any, known_names=(), key: bytes = DEID_KEY) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k).lower() in ID_KEYS:
                out[k] = "[REDACTED]"
            else:
                out[k] = redact_obj(v, known_names, key)
        return out
    if isinstance(obj, (list, tuple)):
        return [redact_obj(v, known_names, key) for v in obj]
    if isinstance(obj, str):
        return redact_text(obj, known_names, key)
    return obj


def _resources(bundle: dict, rtype: str) -> list[dict]:
    return [e["resource"] for e in bundle.get("entry", []) if e.get("resource", {}).get("resourceType") == rtype]


def age_band(birth_date: str, as_of_year: int = AS_OF_YEAR) -> str:
    age = as_of_year - date.fromisoformat(birth_date).year
    if age >= 90:
        return "90+"
    lo = (age // 10) * 10
    return f"{lo}-{lo + 9}"


def minimum_necessary(bundle: dict, key: bytes = DEID_KEY) -> dict:
    """Only what the criteria step needs: no names, contact data, addresses or full dates."""
    patient = _resources(bundle, "Patient")[0]
    member = next((i["value"] for i in patient.get("identifier", []) if i.get("system") == "urn:khp:member"), "")
    names = names_from_patient(patient)
    sr = (_resources(bundle, "ServiceRequest") or [{}])[0]
    return {
        "member_token": pseudonymize_member_id(member, key),
        "age_band": age_band(patient["birthDate"]),
        "sex": patient.get("gender", "unknown"),
        "conditions": [c["code"]["coding"][0]["code"] for c in _resources(bundle, "Condition")],
        "medications": [m.get("medicationCodeableConcept", {}).get("text", "") for m in _resources(bundle, "MedicationRequest")],
        "observations": [{"code": o["code"].get("text", ""), "value": o.get("valueQuantity", {}).get("value"),
                          "unit": o.get("valueQuantity", {}).get("unit")} for o in _resources(bundle, "Observation")],
        "service": sr.get("code", {}).get("text", ""),
        "notes": [redact_text(n["text"], names, key) for n in sr.get("note", [])],
    }


def build_prompt(bundle: dict, policy_text: str, key: bytes = DEID_KEY) -> str:
    ctx = minimum_necessary(bundle, key)
    lines = ["Check the request against the policy. Recommend only.", f"POLICY: {policy_text}"]
    lines += [f"{k.upper()}: {v}" for k, v in ctx.items()]
    return "\n".join(lines)


class RedactingFilter(logging.Filter):
    """Redacts the fully formatted message (msg % args) and any exception text before handlers see it."""

    def __init__(self, known_names=(), key: bytes = DEID_KEY):
        super().__init__()
        self.known_names = list(known_names)
        self.key = key

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_text(record.getMessage(), self.known_names, self.key)
        record.args = None
        if record.exc_info:
            text = logging.Formatter().formatException(record.exc_info)
            record.exc_text = redact_text(text, self.known_names, self.key)
            record.exc_info = None
        for attr, value in list(vars(record).items()):
            if attr not in _STD and isinstance(value, (str, dict, list)):
                setattr(record, attr, redact_obj(value, self.known_names, self.key))
        return True


_STD = set(vars(logging.LogRecord("x", 0, "x", 0, "x", None, None))) | {"message", "asctime"}


def scrub_span_attributes(attrs: dict, known_names=(), key: bytes = DEID_KEY) -> dict:
    out = {}
    for k, v in attrs.items():
        if any(s in k.lower() for s in ("member_id", "patient.name", "ssn", "mrn", "email", "phone")):
            out[k] = "[REDACTED]"
        elif isinstance(v, (dict, list)):
            out[k] = redact_obj(v, known_names, key)
        elif isinstance(v, str):
            out[k] = redact_text(v, known_names, key)
        else:
            out[k] = v
    return out

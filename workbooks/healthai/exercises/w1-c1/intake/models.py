"""PA request contracts (Pydantic v2). TODO: finish the models and the discriminated union (README)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ImagingRequest(BaseModel):
    category: Literal["imaging"]
    member_id: str
    priority: str
    received_at: datetime
    diagnosis_codes: list[str]
    clinical_justification: str = ""
    modality: str
    body_region: str


# TODO: MedicationRequest, InpatientRequest, a shared base with the common fields and validators,
# and PARequest = a discriminated union on "category".
PARequest = ImagingRequest


class CaseOut(BaseModel):
    case_id: str
    category: str
    priority: str
    route: Literal["clinical-review", "eligibility-review"]
    clock: Literal["cms-0057-f", "none"]
    decision_due: datetime | None

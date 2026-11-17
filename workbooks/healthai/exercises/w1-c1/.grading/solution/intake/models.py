"""PA request contracts (Pydantic v2). One model per category, a discriminated union on `category`."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Annotated, Literal, Union

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

ICD10CM = re.compile(r"^[A-Z][0-9][0-9A-Z](\.[0-9A-Z]{1,4})?$")


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    member_id: str = Field(pattern=r"^M-\d{6}$")
    priority: Literal["expedited", "standard"]
    received_at: AwareDatetime
    diagnosis_codes: list[str] = Field(min_length=1)
    clinical_justification: str = ""

    @field_validator("diagnosis_codes")
    @classmethod
    def icd10cm(cls, codes: list[str]) -> list[str]:
        out = []
        for c in codes:
            c = c.strip().upper()
            if not ICD10CM.match(c):
                raise ValueError(f"not an ICD-10-CM code: {c!r}")
            out.append(c)
        return out

    @model_validator(mode="after")
    def expedited_needs_justification(self):
        if self.priority == "expedited" and len(self.clinical_justification) < 20:
            raise ValueError("expedited requests need a clinical justification of at least 20 characters")
        return self


class ImagingRequest(_Base):
    category: Literal["imaging"]
    modality: Literal["mri", "ct", "pet"]
    body_region: str = Field(min_length=2)


class MedicationRequest(_Base):
    category: Literal["medication"]
    drug_name: str = Field(min_length=2)
    hcpcs_code: str | None = Field(default=None, pattern=r"^[A-Z]\d{4}$")
    days_supply: StrictInt = Field(ge=1, le=365)


class InpatientRequest(_Base):
    category: Literal["inpatient"]
    admit_date: date
    expected_los_days: StrictInt = Field(ge=1, le=60)


PARequest = Annotated[Union[ImagingRequest, MedicationRequest, InpatientRequest], Field(discriminator="category")]


class CaseOut(BaseModel):
    case_id: str
    category: str
    priority: str
    route: Literal["clinical-review", "eligibility-review"]
    clock: Literal["cms-0057-f", "none"]
    decision_due: datetime | None

"""Message contract for topic vibration.features (schema v1 and v2)."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class InvalidRecord(ValueError):
    """Raised by parse_record; str(exc) is the quarantine reason."""


class FeatureRecord(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    schema_version: Literal[1, 2] = 1
    device_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,31}$")
    window_start: datetime
    window_s: int = Field(ge=1, le=3600)
    seq: int = Field(ge=0)
    rms: float = Field(ge=0)
    peak: float = Field(ge=0)
    kurtosis: float
    band_energy: list[float] = Field(min_length=4, max_length=4)
    temperature_c: float | None = None

    @field_validator("window_start")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("window_start must carry a UTC offset")
        return v.astimezone(timezone.utc)

    @field_validator("rms", "peak", "kurtosis", "temperature_c")
    @classmethod
    def _finite(cls, v: float | None) -> float | None:
        if v is not None and not math.isfinite(v):
            raise ValueError("must be finite")
        return v

    @field_validator("band_energy")
    @classmethod
    def _bands(cls, v: list[float]) -> list[float]:
        if any((not math.isfinite(x)) or x < 0 for x in v):
            raise ValueError("band energies must be finite and >= 0")
        return v

    @property
    def key(self) -> tuple[str, str]:
        return (self.device_id, self.window_start.strftime("%Y-%m-%dT%H:%M:%SZ"))


def parse_record(raw: bytes) -> FeatureRecord:
    try:
        data = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidRecord(f"not JSON: {exc.__class__.__name__}") from None
    if not isinstance(data, dict):
        raise InvalidRecord("not a JSON object")
    try:
        return FeatureRecord.model_validate(data)
    except ValidationError as exc:
        first = exc.errors()[0]
        loc = ".".join(str(p) for p in first["loc"]) or "record"
        raise InvalidRecord(f"{loc}: {first['msg']}") from None

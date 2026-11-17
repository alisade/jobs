"""Message contract for topic vibration.features (schema v1 and v2).

TODO: implement FeatureRecord and parse_record so that every rule in README.md
"Message contract" holds. Invalid input must raise InvalidRecord with a short,
human-readable reason (it is stored in the quarantine table).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class InvalidRecord(ValueError):
    """Raised by parse_record; str(exc) is the quarantine reason."""


class FeatureRecord(BaseModel):
    # TODO: fields, constraints and validators (see README "Message contract").
    schema_version: int = 1
    device_id: str
    window_start: datetime
    window_s: int
    seq: int
    rms: float
    peak: float
    kurtosis: float
    band_energy: list[float]
    temperature_c: float | None = None

    @property
    def key(self) -> tuple[str, str]:
        """(device_id, window_start as 'YYYY-MM-DDTHH:MM:SSZ' in UTC): the idempotency key."""
        raise NotImplementedError("TODO")


def parse_record(raw: bytes) -> FeatureRecord:
    """Parse one message value. Raise InvalidRecord on anything that breaks the contract."""
    raise NotImplementedError("TODO")

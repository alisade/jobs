import copy

import httpx
import pytest

from intake.app import app, get_eligibility, get_timeout
from intake.eligibility import EligibilityClient

IMAGING = {
    "category": "imaging", "member_id": "M-100201", "priority": "standard",
    "received_at": "2026-11-10T14:30:00-05:00", "diagnosis_codes": ["M54.16"],
    "modality": "mri", "body_region": "lumbar spine",
}
MEDICATION = {
    "category": "medication", "member_id": "M-100202", "priority": "expedited",
    "received_at": "2026-11-10T09:00:00-06:00", "diagnosis_codes": ["k50.90"],
    "clinical_justification": "Active flare with weight loss; delay risks hospitalization.",
    "drug_name": "infliximab", "hcpcs_code": "J1745", "days_supply": 56,
}
INPATIENT = {
    "category": "inpatient", "member_id": "M-100204", "priority": "standard",
    "received_at": "2026-11-10T08:00:00-07:00", "diagnosis_codes": ["I50.23"],
    "admit_date": "2026-11-12", "expected_los_days": 4,
}


@pytest.fixture
def body():
    return lambda which: copy.deepcopy({"imaging": IMAGING, "medication": MEDICATION, "inpatient": INPATIENT}[which])


@pytest.fixture
def fake():
    return EligibilityClient()


@pytest.fixture
async def client(fake):
    app.dependency_overrides[get_eligibility] = lambda: fake
    app.dependency_overrides[get_timeout] = lambda: 0.2
    try:
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
                yield c
    finally:
        app.dependency_overrides.clear()

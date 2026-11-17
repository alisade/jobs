"""FastAPI edge for PA intake. TODO items are listed in README."""

from __future__ import annotations

import itertools
import os
from typing import Annotated

from fastapi import Body, Depends, FastAPI, HTTPException, Request

from .clock import compute_deadline
from .eligibility import EligibilityClient
from .models import CaseOut, PARequest

ELIGIBILITY_TIMEOUT_S = float(os.environ.get("KHP_ELIGIBILITY_TIMEOUT_S", "2.0"))

app = FastAPI(title="KHP PA intake")

# TODO: create and close these in a lifespan handler (app.state), not at import time.
_client = EligibilityClient()
_cases: dict[str, CaseOut] = {}
_seq = itertools.count(1)


def get_eligibility(request: Request) -> EligibilityClient:
    return _client


def get_timeout() -> float:
    return ELIGIBILITY_TIMEOUT_S


@app.post("/v1/pa-requests", status_code=201, response_model=CaseOut)
async def create_request(
    request: Request,
    body: Annotated[PARequest, Body()],
    eligibility: Annotated[EligibilityClient, Depends(get_eligibility)],
    timeout_s: Annotated[float, Depends(get_timeout)],
) -> CaseOut:
    # TODO: Idempotency-Key header, eligibility timeout -> 503
    elig = await eligibility.check(body.member_id)
    due = compute_deadline(body.received_at, body.priority, elig["plan_type"], elig.get("plan_tz", "America/New_York"))
    case = CaseOut(
        case_id=f"PA-{next(_seq):06d}",
        category=body.category,
        priority=body.priority,
        route="clinical-review" if elig["active"] else "eligibility-review",
        clock="none" if due is None else "cms-0057-f",
        decision_due=due,
    )
    _cases[case.case_id] = case
    return case


@app.get("/v1/pa-requests/{case_id}", response_model=CaseOut)
async def get_request(case_id: str, request: Request) -> CaseOut:
    if case_id not in _cases:
        raise HTTPException(404, "case not found")
    return _cases[case_id]

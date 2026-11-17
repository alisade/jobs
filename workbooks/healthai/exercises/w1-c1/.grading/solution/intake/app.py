"""FastAPI edge for PA intake."""

from __future__ import annotations

import asyncio
import hashlib
import itertools
import os
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Request
from pydantic import TypeAdapter

from .clock import compute_deadline
from .eligibility import EligibilityClient
from .models import CaseOut, PARequest

ELIGIBILITY_TIMEOUT_S = float(os.environ.get("KHP_ELIGIBILITY_TIMEOUT_S", "2.0"))
_adapter = TypeAdapter(PARequest)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.eligibility = EligibilityClient()
    app.state.cases = {}
    app.state.idem = {}
    app.state.seq = itertools.count(1)
    try:
        yield
    finally:
        await app.state.eligibility.aclose()


app = FastAPI(title="KHP PA intake", lifespan=lifespan)


def get_eligibility(request: Request) -> EligibilityClient:
    return request.app.state.eligibility


def get_timeout() -> float:
    return ELIGIBILITY_TIMEOUT_S


@app.post("/v1/pa-requests", status_code=201, response_model=CaseOut)
async def create_request(
    request: Request,
    body: Annotated[PARequest, Body()],
    eligibility: Annotated[EligibilityClient, Depends(get_eligibility)],
    timeout_s: Annotated[float, Depends(get_timeout)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> CaseOut:
    st = request.app.state
    fingerprint = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
    if idempotency_key:
        prev = st.idem.get(idempotency_key)
        if prev:
            if prev[0] != fingerprint:
                raise HTTPException(409, "idempotency key reused with a different body")
            return st.cases[prev[1]]
    try:
        async with asyncio.timeout(timeout_s):
            elig = await eligibility.check(body.member_id)
    except TimeoutError:
        raise HTTPException(503, "eligibility timeout")
    due = compute_deadline(body.received_at, body.priority, elig["plan_type"], elig.get("plan_tz", "America/New_York"))
    case = CaseOut(
        case_id=f"PA-{next(st.seq):06d}",
        category=body.category,
        priority=body.priority,
        route="clinical-review" if elig["active"] else "eligibility-review",
        clock="none" if due is None else "cms-0057-f",
        decision_due=due,
    )
    st.cases[case.case_id] = case
    if idempotency_key:
        st.idem[idempotency_key] = (fingerprint, case.case_id)
    return case


@app.get("/v1/pa-requests/{case_id}", response_model=CaseOut)
async def get_request(case_id: str, request: Request) -> CaseOut:
    case = request.app.state.cases.get(case_id)
    if case is None:
        raise HTTPException(404, "case not found")
    return case

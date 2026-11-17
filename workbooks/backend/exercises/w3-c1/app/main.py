"""accounts-svc HTTP API (subset): create accounts and contacts, read an account."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from . import problems
from .db import create_schema, make_engine, make_sessionmaker
from .directory import Directory
from .idempotency import run_idempotent
from .models import Account, Contact
from .problems import ProblemError


class AccountIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    domain: str | None = Field(default=None, max_length=200)


class ContactIn(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+$")
    full_name: str = Field(min_length=1, max_length=200)


def tenant(x_tenant_id: str = Header(min_length=1, max_length=64)) -> str:
    return x_tenant_id


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def account_json(a: Account) -> dict:
    return {"id": a.id, "name": a.name, "domain": a.domain, "industry": a.industry,
            "created_at": a.created_at.isoformat()}


def create_app(db_path: str, directory: Directory | None = None, clock=utcnow) -> FastAPI:  # noqa: ANN001
    engine = make_engine(db_path)

    async def lifespan(app: FastAPI):
        await create_schema(engine)
        yield
        await engine.dispose()

    app = FastAPI(title="accounts-svc", lifespan=lifespan)
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)
    app.state.directory = directory or Directory()
    app.state.clock = clock
    problems.install(app)

    @app.post("/v1/accounts", status_code=201)
    async def create_account(body: AccountIn, request: Request, tenant_id: str = Depends(tenant)):
        async def handler() -> tuple[int, dict]:
            enrich = await app.state.directory.lookup(body.domain)
            async with app.state.sessionmaker() as s:
                a = Account(id=str(uuid.uuid4()), tenant_id=tenant_id, name=body.name, domain=body.domain,
                            industry=enrich["industry"], created_at=app.state.clock())
                s.add(a)
                await s.commit()
                return 201, account_json(a)

        return await run_idempotent(request, tenant_id, handler)

    @app.get("/v1/accounts/{account_id}")
    async def get_account(account_id: str, tenant_id: str = Depends(tenant)):
        async with app.state.sessionmaker() as s:
            a = await s.scalar(select(Account).where(Account.id == account_id, Account.tenant_id == tenant_id))
        if a is None:
            raise ProblemError(404, "Account not found", type_="not-found")
        return account_json(a)

    @app.post("/v1/accounts/{account_id}/contacts", status_code=201)
    async def create_contact(account_id: str, body: ContactIn, request: Request, tenant_id: str = Depends(tenant)):
        async def handler() -> tuple[int, dict]:
            async with app.state.sessionmaker() as s:
                a = await s.scalar(select(Account).where(Account.id == account_id, Account.tenant_id == tenant_id))
                if a is None:
                    return 404, {"type": problems.BASE + "not-found", "title": "Account not found", "status": 404}
                c = Contact(id=str(uuid.uuid4()), tenant_id=tenant_id, account_id=a.id, email=body.email.lower(),
                            full_name=body.full_name, created_at=app.state.clock())
                s.add(c)
                try:
                    await s.commit()
                except IntegrityError:
                    return 409, {"type": problems.BASE + "duplicate-contact", "title": "A contact with this email exists",
                                 "status": 409}
                return 201, {"id": c.id, "account_id": a.id, "email": c.email, "full_name": c.full_name}

        return await run_idempotent(request, tenant_id, handler)

    return app

"""FastAPI front of the tutor agent (Cloud Run service tutor-agent, no public ingress)."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .agent import TutorAgent
from .auth import AuthConfig, AuthError, verify_caller
from .model import TutorModel


class TurnRequest(BaseModel):
    sessionId: str = Field(min_length=1, max_length=128)
    learnerId: str = Field(min_length=1, max_length=64)
    courseId: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=2000)


class TurnResponse(BaseModel):
    reply: str
    toolCalls: list[str]
    refused: bool = False
    withheld: bool = False


def create_app(model: TutorModel, public_key_pem: str, cfg: AuthConfig = AuthConfig()) -> FastAPI:
    app = FastAPI(title="kestrel-tutor-agent")
    agent = TutorAgent(model)

    def caller(authorization: str | None = Header(default=None)) -> dict:
        try:
            return verify_caller(authorization, public_key_pem, cfg)
        except AuthError as e:
            raise HTTPException(status_code=e.status, detail=e.detail,
                                headers={"WWW-Authenticate": "Bearer"} if e.status == 401 else None)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.post("/v1/tutor/turn", response_model=TurnResponse)
    def turn(req: TurnRequest, _claims: dict = Depends(caller)):
        r = agent.run_turn(req.learnerId, req.courseId, req.message)
        return TurnResponse(reply=r.reply, toolCalls=r.tool_calls, refused=r.refused, withheld=r.withheld)

    return app

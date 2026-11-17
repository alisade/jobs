"""FastAPI front of the tutor agent (Cloud Run service tutor-agent, no public ingress)."""

from __future__ import annotations

from fastapi import FastAPI, Header
from pydantic import BaseModel

from .agent import TutorAgent
from .auth import AuthConfig
from .model import TutorModel


class TurnRequest(BaseModel):
    sessionId: str
    learnerId: str
    courseId: str
    message: str


class TurnResponse(BaseModel):
    reply: str
    toolCalls: list[str]
    refused: bool = False
    withheld: bool = False


def create_app(model: TutorModel, public_key_pem: str, cfg: AuthConfig = AuthConfig()) -> FastAPI:
    app = FastAPI(title="kestrel-tutor-agent")
    agent = TutorAgent(model)

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    @app.post("/v1/tutor/turn", response_model=TurnResponse)
    def turn(req: TurnRequest, authorization: str | None = Header(default=None)):
        # TODO(w4-c1): authenticate the caller; validate the request (see README)
        r = agent.run_turn(req.learnerId, req.courseId, req.message)
        return TurnResponse(reply=r.reply, toolCalls=r.tool_calls, refused=r.refused, withheld=r.withheld)

    return app

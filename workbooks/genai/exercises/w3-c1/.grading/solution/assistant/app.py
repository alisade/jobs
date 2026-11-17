"""Assistant HTTP API. Reference solution.

Auth is stubbed: the edge gateway validates the customer's session and forwards X-User-Id.
"""

from __future__ import annotations

import secrets
import time
from typing import Callable

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .agent import Agent
from .llm import LLMClient
from .store import Store


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = None


class PendingOut(BaseModel):
    action_id: str
    summary: str


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    pending_action: PendingOut | None = None
    truncated: bool = False


class ConfirmRequest(BaseModel):
    conversation_id: str


def create_app(llm: LLMClient, store: Store | None = None, clock: Callable[[], float] = time.monotonic) -> FastAPI:
    agent = Agent(llm=llm, store=store or Store(), clock=clock)
    owners: dict[str, str] = {}
    app = FastAPI(title="kestrel-assistant")
    app.state.agent = agent

    @app.post("/chat", response_model=ChatResponse)
    def chat(body: ChatRequest, x_user_id: str = Header(...)) -> ChatResponse:
        cid = body.conversation_id or "c-" + secrets.token_hex(6)
        if owners.setdefault(cid, x_user_id) != x_user_id:
            raise HTTPException(404, "conversation not found")
        r = agent.chat(x_user_id, cid, body.message)
        p = PendingOut(action_id=r.pending_action.action_id, summary=r.pending_action.summary) if r.pending_action else None
        return ChatResponse(conversation_id=cid, reply=r.reply, pending_action=p, truncated=r.truncated)

    @app.post("/actions/{action_id}/confirm")
    def confirm(action_id: str, body: ConfirmRequest, x_user_id: str = Header(...)) -> dict:
        try:
            result = agent.confirm(x_user_id, body.conversation_id, action_id)
        except (LookupError, PermissionError):
            raise HTTPException(404, "action not found")  # do not reveal other users' actions
        except TimeoutError:
            raise HTTPException(410, "confirmation expired; ask the assistant again")
        except RuntimeError as e:
            raise HTTPException(409, str(e))
        return {"status": "done", "result": result}

    return app

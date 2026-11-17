"""Assistant HTTP API.

Auth is stubbed: the edge gateway validates the customer's session and forwards X-User-Id.
"""

from __future__ import annotations

import secrets
import time
from typing import Callable

from fastapi import FastAPI, Header
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
    app = FastAPI(title="kestrel-assistant")
    app.state.agent = agent

    @app.post("/chat", response_model=ChatResponse)
    def chat(body: ChatRequest, x_user_id: str = Header(...)) -> ChatResponse:
        cid = body.conversation_id or "c-" + secrets.token_hex(6)
        r = agent.chat(x_user_id, cid, body.message)
        return ChatResponse(conversation_id=cid, reply=r.reply)

    # TODO: POST /actions/{action_id}/confirm (see README.md for status codes), and
    # return pending_action / truncated from /chat. A conversation belongs to one user.

    return app

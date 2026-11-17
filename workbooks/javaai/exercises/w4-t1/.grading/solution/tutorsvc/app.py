"""tutor-agent HTTP front (Cloud Run). One uvicorn worker per instance, as in the Dockerfile."""

from __future__ import annotations

import time

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .gemini import BlockingGemini


class Turn(BaseModel):
    learnerId: str
    message: str = Field(min_length=1, max_length=2000)


def create_app(client: BlockingGemini | None = None) -> FastAPI:
    app = FastAPI(title="kestrel-tutor-agent")
    app.state.client = client or BlockingGemini()

    @app.get("/healthz")
    async def healthz():
        return {"ok": True}

    # A plain def: FastAPI runs it in the threadpool, so a blocking model call waits on a worker
    # thread instead of freezing the event loop that serves every other request on the instance.
    # (With an async SDK client, keep async def and await the call instead.)
    @app.post("/v1/tutor/turn")
    def turn(req: Turn):
        started = time.perf_counter()
        reply = app.state.client.generate_content(req.message)
        return {"reply": reply, "modelMs": round(1000 * (time.perf_counter() - started))}

    return app


app = create_app()

"""FastAPI front of the quiz service (Cloud Run service quiz-gen)."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import service
from .gemini import RateLimited, ReplayGemini


class GenerateRequest(BaseModel):
    lessonId: str = Field(min_length=1)
    count: int = Field(default=3, ge=1, le=10)


def create_app(client=None) -> FastAPI:
    app = FastAPI(title="kestrel-quiz-gen")
    app.state.client = client or ReplayGemini()

    @app.post("/quiz/generate")
    def generate(req: GenerateRequest):
        try:
            return service.generate_quiz(app.state.client, req.lessonId, req.count)
        except KeyError as e:
            if e.args and e.args[0] == req.lessonId:
                raise HTTPException(status_code=404, detail="unknown lesson")
            raise
        except RateLimited:
            raise HTTPException(status_code=503, detail="model capacity exhausted, retry later", headers={"Retry-After": "5"})

    return app


app = create_app()

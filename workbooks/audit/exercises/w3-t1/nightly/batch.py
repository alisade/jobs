"""One nightly invocation: resume the CM-03 session and test the next batch. Do not edit unless your fix needs it."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from google.adk import Agent, Runner
from google.adk.sessions import DatabaseSessionService
from google.genai import types

from . import tools
from .policy_llm import PolicyLlm

APP, USER, SESSION = "controlpilot", "ia-nightly", "cm03-2026Q3"


def build_agent() -> Agent:
    return Agent(name="cm03_nightly", model=PolicyLlm(),
                 instruction="Call next_batch, test every change it returns with test_change, then stop.",
                 tools=[tools.next_batch, tools.test_change])


async def run_once(run_dir: Path) -> str:
    run_dir.mkdir(parents=True, exist_ok=True)
    os.environ["NIGHTLY_RUN_DIR"] = str(run_dir)
    service = DatabaseSessionService(db_url=f"sqlite+aiosqlite:///{run_dir / 'sessions.db'}")
    runner = Runner(app_name=APP, agent=build_agent(), session_service=service)
    session = await service.get_session(app_name=APP, user_id=USER, session_id=SESSION)
    if session is None:
        session = await service.create_session(app_name=APP, user_id=USER, session_id=SESSION)
    final = ""
    async for ev in runner.run_async(user_id=USER, session_id=SESSION,
                                     new_message=types.Content(role="user", parts=[types.Part(text="Run the nightly CM-03 batch.")])):
        if ev.content and ev.content.parts:
            final = "".join(p.text for p in ev.content.parts if p.text) or final
    return final


def main() -> None:
    print(asyncio.run(run_once(Path(os.environ.get("NIGHTLY_RUN_DIR", "run")))))


if __name__ == "__main__":
    main()

"""Build and run the evidence-review agent (Google ADK) for one sampled change."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from google.adk import Agent, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .evidence import evidence_text
from .store import GrcStore
from .tools import make_tools

CONFIG = Path(__file__).resolve().parents[1] / "config" / "evidence_reviewer.yaml"
logging.getLogger("google_adk").setLevel(logging.ERROR)


@dataclass
class ReviewResult:
    change_id: str
    final_text: str
    trace: list[dict] = field(default_factory=list)  # {"tool", "args", "executed", "response"}
    flags: list[dict] = field(default_factory=list)  # {"kind", ...}


def load_config() -> dict:
    return yaml.safe_load(CONFIG.read_text())


def build_agent(llm, change_id: str, store: GrcStore, evidence_dir: str | Path) -> Agent:
    cfg = load_config()
    tools = make_tools(store, evidence_dir)
    instruction = cfg["instruction"] + "\nEVIDENCE:\n" + evidence_text(evidence_dir, change_id)
    return Agent(name=cfg["name"], model=llm, instruction=instruction, tools=[tools[t] for t in cfg["tools"]])


async def _run(agent: Agent, message: str, result: ReviewResult) -> None:
    ss = InMemorySessionService()
    runner = Runner(app_name="controlpilot", agent=agent, session_service=ss)
    session = await ss.create_session(app_name="controlpilot", user_id="svc-controlpilot")
    pending: dict[str, dict] = {}
    async for ev in runner.run_async(user_id="svc-controlpilot", session_id=session.id,
                                     new_message=types.Content(role="user", parts=[types.Part(text=message)])):
        for p in (ev.content.parts if ev.content else []) or []:
            if p.function_call:
                entry = {"tool": p.function_call.name, "args": dict(p.function_call.args or {}), "executed": False, "response": None}
                result.trace.append(entry)
                pending[p.function_call.name] = entry
            elif p.function_response:
                entry = pending.pop(p.function_response.name, None)
                if entry is not None:
                    resp = dict(p.function_response.response or {})
                    entry["response"] = resp
                    entry["executed"] = "error" not in resp
            elif p.text and ev.is_final_response():
                result.final_text = p.text


def review(llm, change_id: str, store: GrcStore, evidence_dir: str | Path) -> ReviewResult:
    agent = build_agent(llm, change_id, store, evidence_dir)
    open_exc = {k: v["attribute"] for k, v in store.exceptions_for(change_id).items() if v["status"] == "open"}
    message = f"Change {change_id}. Open exceptions: {json.dumps(open_exc)}."
    result = ReviewResult(change_id=change_id, final_text="")
    asyncio.run(_run(agent, message, result))
    return result

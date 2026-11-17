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

from .evidence import evidence_files, evidence_text, load_layout
from .screen import screen_evidence
from .store import GrcStore
from .tools import READ_ONLY_TOOLS, make_tools

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
    """The evidence agent gets read-only tools only; the instruction is static (no evidence in it)."""
    cfg = load_config()
    wanted = list(cfg["tools"])
    bad = [t for t in wanted if t not in READ_ONLY_TOOLS]
    if bad:
        raise ValueError(f"evidence agent may only have read-only tools, config asks for {bad}")
    tools = make_tools(store, evidence_dir)
    return Agent(name=cfg["name"], model=llm, instruction=cfg["instruction"], tools=[tools[t] for t in wanted])


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
    result = ReviewResult(change_id=change_id, final_text="")
    for f in evidence_files(evidence_dir, change_id):
        for flag in screen_evidence(load_layout(f)):
            result.flags.append(dict(flag, document=f.name))
    # evidence goes in the user turn, delimited, as data
    message = (f"Change {change_id}. Open exceptions: {json.dumps(open_exc)}.\n"
               f"<evidence change_id=\"{change_id}\">\n{evidence_text(evidence_dir, change_id)}\n</evidence>")
    asyncio.run(_run(agent, message, result))
    allowed = {t.__name__ if callable(t) else getattr(t, "name", "") for t in agent.tools}
    for t in result.trace:
        if t["tool"] not in allowed:
            result.flags.append({"kind": "unauthorized_tool_attempt", "tool": t["tool"], "args": t["args"]})
    return result

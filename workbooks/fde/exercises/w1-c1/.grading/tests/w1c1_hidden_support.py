"""Helpers shared by the tests: the blueprint's real prompt halves, tool list and executor
over the retail mock, plus a fake client loaded from the recorded fixtures."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from retail.api.mock_retail import MockRetail

from agent_loop import FakeAnthropic, load_script
from commerce_common.skills import SkillRegistry
from shopping_agent import (
    PageContext,
    ShoppingAgentConfig,
    ShoppingSessionContext,
    ShoppingSessionState,
)
from shopping_agent.executor import ShoppingToolExecutor
from shopping_agent.prompt import build_dynamic_context, build_static_system
from shopping_agent.tools.registry import build_tools

MODEL = "claude-sonnet-5"
CONFIG = ShoppingAgentConfig()
STATIC = build_static_system(CONFIG, SkillRegistry([]))
TOOLS = build_tools(CONFIG, skill_names=[])


def dynamic(page: str = "home") -> str:
    return build_dynamic_context(
        preferences=None, memory_facts=[], cart=None, page=PageContext(page_type=page)
    )


@dataclass
class Rig:
    client: FakeAnthropic
    executor: Any
    backend: MockRetail
    session: ShoppingSessionContext

    def kwargs(self, **over: Any) -> dict[str, Any]:
        base = dict(
            model=MODEL,
            static_system=STATIC,
            dynamic_context=dynamic(),
            tools=TOOLS,
            messages=[],
            user_text="hi",
        )
        base.update(over)
        return base


def make_rig(script: str | list[dict[str, Any]]) -> Rig:
    responses = load_script(script) if isinstance(script, str) else script
    backend = MockRetail()
    session = ShoppingSessionContext(session_id="sess-w1c1", user_id="demo-user")
    executor = ShoppingToolExecutor(
        backend=backend,
        config=CONFIG,
        skills=SkillRegistry([]),
        session=session,
        state=ShoppingSessionState(),
    )
    return Rig(FakeAnthropic(responses), executor, backend, session)


class SlowExecutor:
    """Delays each named tool by ``delays[name]`` seconds, then delegates."""

    def __init__(self, inner: Any, delays: dict[str, float]) -> None:
        self.inner = inner
        self.delays = delays
        self.order: list[str] = []

    async def execute(self, name: str, tool_input: dict[str, Any] | None):
        await asyncio.sleep(self.delays.get(name, 0.0))
        self.order.append(name)
        return await self.inner.execute(name, tool_input)


def tool_results(request: dict[str, Any]) -> list[dict[str, Any]]:
    """The tool_result blocks of the request's last user message."""
    last = request["messages"][-1]
    assert last["role"] == "user"
    return [b for b in last["content"] if isinstance(b, dict) and b.get("type") == "tool_result"]

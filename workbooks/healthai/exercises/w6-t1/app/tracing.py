"""A tiny tracer with an exporter that scrubs span attributes (stand-in for OpenTelemetry)."""

from __future__ import annotations

import contextlib
import json

from .redact import redact


def scrub_attributes(attrs: dict) -> dict:
    # TODO(SEC-311 follow-up): scrub nested dict attributes too. We only emit flat attributes today.
    return {k: redact(v) if isinstance(v, str) else v for k, v in attrs.items()}


class Span:
    def __init__(self, name: str, attrs: dict):
        self.name, self.attributes, self.events = name, attrs, []


class Tracer:
    def __init__(self):
        self.spans: list[Span] = []
        self._stack: list[Span] = []

    def current(self):
        return self._stack[-1] if self._stack else None

    @contextlib.contextmanager
    def span(self, name: str, **attrs):
        s = Span(name, attrs)
        self._stack.append(s)
        try:
            yield s
        finally:
            self._stack.pop()
            self.spans.append(s)

    def export(self) -> list[dict]:
        return [{"name": s.name, "attributes": scrub_attributes(s.attributes), "events": s.events} for s in self.spans]

    def reset(self):
        self.spans.clear()
        self._stack.clear()


TRACER = Tracer()


def export_json(path) -> None:
    with open(path, "w") as fh:
        json.dump(TRACER.export(), fh, indent=1)

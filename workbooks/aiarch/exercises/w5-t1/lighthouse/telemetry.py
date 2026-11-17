"""Tracing setup (works as shipped). In prod ADOT exports to CloudWatch Transaction Search; in
tests an in-memory exporter collects finished spans."""
from __future__ import annotations

from opentelemetry import propagate, trace
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

_EXPORTER: InMemorySpanExporter | None = None


def setup() -> InMemorySpanExporter:
    """Install the provider once per process and return the exporter (cleared on each call)."""
    global _EXPORTER
    if _EXPORTER is None:
        _EXPORTER = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(_EXPORTER))
        trace.set_tracer_provider(provider)
        propagate.set_global_textmap(CompositePropagator([TraceContextTextMapPropagator(), W3CBaggagePropagator()]))
    _EXPORTER.clear()
    return _EXPORTER

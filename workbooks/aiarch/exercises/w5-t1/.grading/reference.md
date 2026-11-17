# Reference: aiarch/w5-t1

Root cause: `ThreadPoolExecutor` workers do not inherit contextvars, so the OTEL current span is
lost; execute_tool spans start new traces and propagate those. Fix: submit with
`contextvars.copy_context().run` per task (or capture `context.get_current()` and
`context.attach` in the worker). Propagators and sampling are red herrings.

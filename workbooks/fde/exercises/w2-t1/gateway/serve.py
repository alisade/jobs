"""uvicorn entry point with the gateway's production log format."""

from __future__ import annotations

import logging

from starlette.applications import Starlette

from .app import create_app


def app_factory() -> Starlette:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return create_app()

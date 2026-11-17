import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.shared.memory import create_connected_server_and_client_session  # noqa: E402

from progress_mcp.catalog_api import CatalogApi  # noqa: E402
from progress_mcp.server import build_server  # noqa: E402


@asynccontextmanager
async def session(learner_id="lrn-ada", api=None):
    api = api or CatalogApi()
    server = build_server(api, learner_id)
    async with create_connected_server_and_client_session(server._mcp_server) as client:
        yield client, api


def payload(result):
    """Parse the JSON text a tool returned (FastMCP serialises dict/list results as JSON text)."""
    texts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
    try:
        return json.loads(texts[0]) if len(texts) == 1 else [json.loads(t) for t in texts]
    except json.JSONDecodeError:
        return texts[0]

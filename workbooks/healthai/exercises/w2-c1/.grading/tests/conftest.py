import grpc
import pytest

from criteria.server import serve
from criteria.stubs import pb2_grpc


@pytest.fixture
async def start():
    opened = []

    async def _start(fhir, **kwargs):
        server, port = await serve(fhir, **kwargs)
        channel = grpc.aio.insecure_channel(f"127.0.0.1:{port}")
        opened.append((server, channel))
        return pb2_grpc.CriteriaServiceStub(channel)

    try:
        yield _start
    finally:
        for server, channel in opened:
            await channel.close()
            await server.stop(0)

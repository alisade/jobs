import grpc
import pytest

from criteria.fhir import FakeFhir
from criteria.server import serve
from criteria.stubs import pb2_grpc


@pytest.fixture
def fhir():
    return FakeFhir()


@pytest.fixture
async def stub(fhir):
    server, port = await serve(fhir, check_timeout_s=0.5)
    channel = grpc.aio.insecure_channel(f"127.0.0.1:{port}")
    try:
        yield pb2_grpc.CriteriaServiceStub(channel)
    finally:
        await channel.close()
        await server.stop(0)


"""Fixtures shared by visible and hidden tests."""
import pytest

from assistant_tools import audit
from assistant_tools.session import Session


@pytest.fixture(autouse=True)
def clean_audit():
    audit.AUDIT.clear()
    yield
    audit.AUDIT.clear()


@pytest.fixture()
def amer():
    return Session(agent_id="sales-assistant", user_id="u-jlee", tenant_id="bu-amer", trace_id="t-amer-1")


@pytest.fixture()
def emea():
    return Session(agent_id="sales-assistant", user_id="u-ksvensson", tenant_id="bu-emea", trace_id="t-emea-1")

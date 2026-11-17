"""Visible checks for the Contoso Parts connector. More checks run at grading time."""
from openapi_spec_validator import validate

from connector_checks import load_props, load_swagger, operations


def test_swagger_is_valid_openapi_2():
    spec = load_swagger()
    assert spec.get("swagger") == "2.0", "custom connectors use OpenAPI (Swagger) 2.0"
    validate(spec)


def test_host_basepath_schemes():
    spec = load_swagger()
    assert "://" not in spec["host"] and "/" not in spec["host"], "host is a bare host name"
    assert spec["basePath"].startswith("/")
    assert spec["schemes"] == ["https"]


def test_operation_ids_unique_and_identifier_like():
    ids = [op.get("operationId", "") for _, _, op in operations(load_swagger())]
    assert len(ids) == len(set(ids))
    for i in ids:
        assert i and i.isidentifier() and i[0].isupper(), f"operationId {i!r} should be PascalCase, no spaces"


def test_api_properties_uses_entra_id():
    token = load_props()["properties"]["connectionParameters"]["token"]
    assert token["type"].lower() == "oauthsetting"
    assert token["oAuthSettings"]["identityProvider"] == "aad"

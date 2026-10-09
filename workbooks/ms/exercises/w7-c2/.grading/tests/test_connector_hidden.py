"""Hidden checks for ms/w7-c2. Rules come from the custom connector OpenAPI extension docs,
the certification requirements and the swagger validator rule list on learn.microsoft.com."""
import re

import pytest
from openapi_spec_validator import validate

from connector_checks import (get_path, load_props, load_swagger, op_by_id, operations, params,
                              resolve, walk_properties)

SPEC = load_swagger()
PROPS = load_props()["properties"]
GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
REQUIRED_OPS = {"ListParts", "GetPart", "CreateReorder", "ListWarehouses", "ListCategories"}


def _ops():
    return list(operations(SPEC))


def test_openapi_2_valid():
    validate(SPEC)


def test_required_operations_exist():
    ids = {op.get("operationId") for _, _, op in _ops()}
    missing = REQUIRED_OPS - ids
    assert not missing, f"missing operations: {sorted(missing)}"


def test_every_operation_has_summary_and_description():
    for path, m, op in _ops():
        s = op.get("summary", "")
        assert s and len(s) <= 80, f"{op.get('operationId')}: summary missing or longer than 80 chars"
        assert re.fullmatch(r"[A-Za-z0-9 ()]+", s), f"{op.get('operationId')}: summary must be alphanumeric/parentheses"
        d = op.get("description", "")
        assert d and d.rstrip()[-1] in ".!?", f"{op.get('operationId')}: description must be a sentence ending in punctuation"
        assert op.get("x-ms-visibility") in ("important", "advanced", "internal"), f"{op.get('operationId')}: set x-ms-visibility"


def test_every_parameter_has_summary_and_description():
    for path, m, op in _ops():
        for p in params(SPEC, op, SPEC["paths"][path]):
            assert p.get("x-ms-summary"), f"{op.get('operationId')}: parameter {p.get('name')} needs x-ms-summary"
            assert p.get("description"), f"{op.get('operationId')}: parameter {p.get('name')} needs description"


def test_path_parameters_required():
    for path, m, op in _ops():
        for p in params(SPEC, op, SPEC["paths"][path]):
            if p.get("in") == "path":
                assert p.get("required") is True


def test_internal_required_parameters_have_defaults():
    for path, m, op in _ops():
        for p in params(SPEC, op, SPEC["paths"][path]):
            if p.get("x-ms-visibility") == "internal" and p.get("required"):
                assert "default" in p, f"{op.get('operationId')}: internal+required parameter {p['name']} needs a default"


def test_response_properties_have_summaries():
    for path, m, op in _ops():
        for code, resp in op.get("responses", {}).items():
            schema = resolve(SPEC, resp).get("schema")
            if not schema:
                continue
            for name, prop in walk_properties(SPEC, schema):
                assert prop.get("x-ms-summary"), f"{op.get('operationId')} {code}: property {name} needs x-ms-summary"


def test_success_responses_have_schemas_and_no_default_schema():
    for path, m, op in _ops():
        responses = op.get("responses", {})
        ok = [c for c in responses if str(c).startswith("2")]
        assert ok, f"{op.get('operationId')}: no 2xx response"
        for c in ok:
            if str(c) != "204":
                assert resolve(SPEC, responses[c]).get("schema"), f"{op.get('operationId')} {c}: define the exact response schema"
        if "default" in responses:
            assert "schema" not in resolve(SPEC, responses["default"]), \
                f"{op.get('operationId')}: don't put an exact schema on a default response"


def test_list_parts_is_pageable():
    path, m, op = op_by_id(SPEC, "ListParts")
    pg = op.get("x-ms-pageable")
    assert pg and pg.get("nextLinkName") in ("nextLink", "@odata.nextLink"), \
        "x-ms-pageable.nextLinkName must be 'nextLink' or '@odata.nextLink'"
    schema = resolve(SPEC, op["responses"]["200"]["schema"])
    props = schema.get("properties", {})
    assert pg["nextLinkName"] in props, "the 200 schema must contain the nextLinkName property"
    assert resolve(SPEC, props.get("value", {})).get("type") == "array", "items must be in a 'value' array"


def _check_dynamic_values(dv, consumer):
    assert dv, f"{consumer}: add x-ms-dynamic-values"
    target = op_by_id(SPEC, dv.get("operationId", ""))
    assert target, f"{consumer}: dynamic values operation {dv.get('operationId')} not found"
    tpath, tm, top = target
    assert tm == "get", "dynamic values operations should be GETs"
    assert top.get("x-ms-visibility") == "internal", f"{dv['operationId']} should be internal (hidden from makers)"
    assert "parameters" in dv, "x-ms-dynamic-values.parameters is required"
    schema = resolve(SPEC, top["responses"]["200"]["schema"])
    coll = get_path(schema, SPEC, dv["value-collection"]) if dv.get("value-collection") else schema
    assert coll is not None and coll.get("type") == "array", "value-collection must point to an array"
    item = resolve(SPEC, coll["items"])
    for k in ("value-path", "value-title"):
        assert dv.get(k), f"{consumer}: set {k}"
        assert dv[k] in (item.get("properties") or {}), f"{consumer}: {k} '{dv[k]}' not in the item schema"
    # every required parameter of the target must be supplied
    for p in params(SPEC, top, SPEC["paths"][tpath]):
        if p.get("required") and "default" not in p:
            assert p["name"] in dv["parameters"], f"{consumer}: dynamic call misses required parameter {p['name']}"


def test_warehouse_dropdown():
    body = resolve(SPEC, SPEC["definitions"]["ReorderRequest"])
    _check_dynamic_values(body["properties"]["warehouseCode"].get("x-ms-dynamic-values"), "warehouseCode")


def test_category_dropdown():
    path, m, op = op_by_id(SPEC, "ListParts")
    cat = next(p for p in params(SPEC, op) if p.get("name") == "category")
    _check_dynamic_values(cat.get("x-ms-dynamic-values"), "category")


def test_reorder_body_contract():
    body = resolve(SPEC, SPEC["definitions"]["ReorderRequest"])
    assert set(body.get("required", [])) >= {"quantity", "warehouseCode"}
    q = body["properties"]["quantity"]
    assert q.get("type") == "integer" and q.get("minimum", 0) >= 1
    path, m, op = op_by_id(SPEC, "CreateReorder")
    assert m == "post" and "201" in op["responses"]
    assert resolve(SPEC, op["responses"]["201"]).get("schema"), "201 must return the created reorder"


def test_oauth2_security_definition():
    sd = SPEC.get("securityDefinitions", {})
    oauth = [v for v in sd.values() if v.get("type") == "oauth2"]
    assert oauth, "Entra ID auth is declared as an oauth2 security definition"
    assert oauth[0].get("flow") == "accessCode"
    assert not [v for v in sd.values() if v.get("type") == "apiKey"], "drop the function-key apiKey scheme"


def test_connection_parameters_entra():
    token = PROPS["connectionParameters"]["token"]
    s = token["oAuthSettings"]
    assert s["identityProvider"] == "aad"
    assert GUID.match(s.get("clientId", "")), "clientId is the Entra app registration (GUID)"
    assert "clientSecret" not in s, "never commit the client secret into apiProperties.json"
    cp = {k.lower(): v for k, v in (s.get("customParameters") or {}).items()}
    for k in ("loginuri", "tenantid", "resourceuri"):
        assert k in cp, f"customParameters must include {k}"
    assert cp["loginuri"]["value"].startswith("https://login.")
    assert cp["resourceuri"]["value"] == "api://contoso-parts-api", "resource is the Function app's App ID URI"
    assert s.get("redirectMode") == "GlobalPerConnector", "use the per-connector redirect URI"


def test_policy_template_sets_caller_header():
    pts = PROPS.get("policyTemplateInstances") or []
    sh = [p for p in pts if p.get("templateId") == "setheader"]
    assert sh, "add a setheader policy template instance"
    prm = sh[0]["parameters"]
    assert prm.get("x-ms-apimTemplateParameter.name") == "x-contoso-caller"
    assert prm.get("x-ms-apimTemplateParameter.value") == "power-platform"
    assert prm.get("x-ms-apimTemplateParameter.existsAction") == "override"
    assert prm.get("x-ms-apimTemplate-policySection") == "Request"


def test_brand_color():
    c = PROPS.get("iconBrandColor", "")
    assert re.fullmatch(r"#[0-9a-fA-F]{6}", c)
    assert c.lower() not in ("#ffffff", "#007ee5"), "brand color must not be white or the default #007ee5"


@pytest.mark.parametrize("field", ["publisher", "stackOwner"])
def test_publisher_fields(field):
    assert PROPS.get(field)

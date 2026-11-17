import re
from pathlib import Path

import cli_lint

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = (ROOT / "config/migrate-security.cli").read_text()
OPS = [o for o in cli_lint.parse(SCRIPT) if not o.get("unparsed")]


def ops(typ, subsystem="elytron"):
    return [o for o in OPS if o["subsystem"] == subsystem and o["type"] == typ and o["op"] == "add" and not o["child"]]


def one(typ, subsystem="elytron"):
    found = ops(typ, subsystem)
    assert found, f"no {subsystem} {typ} is created"
    return found[0]


def flat(s):
    return re.sub(r"\s+", "", s)


def test_no_vault_and_secret_from_credential_store():
    assert "VAULT::" not in SCRIPT
    dc = one("dir-context")
    a = flat(dc["args"])
    assert "credential-reference={store=claimdesk-cs" in a and "alias=ldap-bind" in a
    assert "clear-text" not in a


def test_dir_context_points_at_the_same_directory():
    a = flat(one("dir-context")["args"])
    assert 'url="ldaps://ldap-vip.corvane.local:636"' in a or "url=ldaps://ldap-vip.corvane.local:636" in a
    assert "uid=svc-claimdesk,ou=service,dc=corvane,dc=local" in a


def test_realm_finds_users_like_the_old_module():
    a = flat(one("ldap-realm")["args"])
    assert "rdn-identifier=uid" in a
    assert "search-base-dn=\"ou=people,dc=corvane,dc=local\"" in a or "search-base-dn=ou=people,dc=corvane,dc=local" in a


def test_group_lookup_keeps_role_recursion():
    a = flat(one("ldap-realm")["args"])
    assert "ou=groups,dc=corvane,dc=local" in a and "(member={1})" in a
    assert "from=cn" in a
    assert re.search(r"role-recursion=2\b", a), "roleRecursion=2 in the old module: nested groups must still grant roles"


def test_roles_decoded_from_the_mapped_attribute():
    realm = flat(one("ldap-realm")["args"])
    to = re.search(r"to=([\w-]+)", realm).group(1)
    dec = one("simple-role-decoder")
    assert dec["attrs"].get("attribute") == to


def test_group_to_role_mapping_preserved():
    a = flat(one("mapped-role-mapper")["args"])
    for grp, role in [("claims-users", "CLAIMS_USER"), ("claims-admins", "CLAIMS_ADMIN"),
                      ("claims-supervisors", "CLAIMS_SUPERVISOR"), ("claims-auditors", "AUDITOR")]:
        assert f"{grp}=[{role}]" in a, f"{grp} must map to {role}"


def test_security_domain_wires_realm_decoder_and_mapper():
    sd = one("security-domain")
    a = flat(sd["args"])
    assert "role-decoder=" + one("simple-role-decoder")["name"] in a
    assert "role-mapper=" + one("mapped-role-mapper")["name"] in a
    assert "default-realm=" + one("ldap-realm")["name"] in a
    assert "permission-mapper=" in a


def test_form_authentication_factory():
    f = one("http-authentication-factory")
    a = flat(f["args"])
    assert "mechanism-name=FORM" in a
    assert "security-domain=" + one("security-domain")["name"] in a


def test_undertow_maps_the_name_the_war_uses():
    war = re.search(r"<security-domain>([^<]+)</security-domain>", (ROOT / "deploy/WEB-INF/jboss-web.xml").read_text()).group(1).strip()
    asd = [o for o in ops("application-security-domain", "undertow") if o["name"] == war]
    assert asd, f"no undertow application-security-domain named {war!r} (the name in jboss-web.xml)"
    a = flat(asd[0]["args"])
    assert "http-authentication-factory=" + one("http-authentication-factory")["name"] in a or \
        "security-domain=" + one("security-domain")["name"] in a


def test_applied_atomically_then_reloaded():
    lines = [l.strip() for l in SCRIPT.splitlines() if l.strip() and not l.strip().startswith("#")]
    assert lines[0] == "batch" and "run-batch" in lines and lines[-1] == "reload"

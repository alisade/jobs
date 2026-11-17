"""Hidden checks: coverage of the touchpoints a careful reverse engineer finds, and precision."""

import pytest

import inventory_check as ic

INV = ic.load()


def by(section, key):
    return [i for i in INV[section] if key(i)]


REQUIRED_DB = {
    "CLAIM": None, "CLAIM_NOTE": None, "CLAIM_ARCHIVE": "ClaimDao.java", "RESERVE_LINE": None,
    "PAYMENT": "orm.xml", "USER_ROLE": "queries.properties", "ADJUSTER": "queries.properties",
}


@pytest.mark.parametrize("table,must_cite", sorted(REQUIRED_DB.items()))
def test_db_table_found_with_its_real_source(table, must_cite):
    hits = [i for i in INV["db_objects"] if ic.db_key(i) == table]
    assert hits, f"database touchpoint {table} missing from db_objects"
    quotes = " ".join(e["quote"].upper() for i in hits for e in i["evidence"])
    assert table in quotes, f"{table}: no evidence quote actually shows the name"
    if must_cite:
        assert any(must_cite in ic.files_of(i) for i in hits), f"{table}: cite where the mapping/SQL really lives ({must_cite})"


def test_stored_procedure_found():
    procs = [i for i in INV["db_objects"] if "PKG_RESERVE" in i.get("name", "").upper()]
    assert procs and procs[0]["kind"] == "procedure" and "execute" in procs[0]["access"]


def test_archive_purge_is_a_delete():
    arch = [i for i in INV["db_objects"] if ic.db_key(i) == "CLAIM_ARCHIVE"]
    assert any("delete" in i["access"] for i in arch), "the weekly cron deletes from the archive tables"


def test_no_invented_db_objects():
    text = ic.all_app_text()
    for i in INV["db_objects"]:
        assert ic.db_key(i) in text, f"{i['name']} does not appear anywhere in app/"


REQUIRED_INTEGRATIONS = {
    "ldap": {"LdapGroupFilter.java", "claimdesk.properties"},
    "http": {"FraudClient.java", "datasource-claimdesk.cli"},
    "soap": {"PolicyAdminClient.java"},
    "smtp": {"MailNotifier.java"},
    "jms": {"PaymentServlet.java"},
    "sftp": {"NightlyReinsuranceExport.java"},
}


@pytest.mark.parametrize("protocol,files", sorted(REQUIRED_INTEGRATIONS.items()))
def test_live_integration_found(protocol, files):
    hits = [i for i in INV["integrations"] if i["protocol"] == protocol and i["status"] == "live"]
    assert hits, f"live {protocol} integration missing"
    cited = set().union(*(ic.files_of(i) for i in hits))
    missing = files - cited
    assert not missing, f"{protocol}: trace the endpoint to where it is defined; also cite {sorted(missing)}"


def test_dead_code_not_reported_as_live():
    for i in INV["integrations"]:
        if "LegacyFaxGateway.java" in ic.files_of(i) or "fax" in i["name"].lower():
            assert i["status"] == "dead", "LegacyFaxGateway is unreferenced dead code"


def test_fail_open_fraud_check_noted():
    http = [i for i in INV["integrations"] if i["protocol"] == "http"]
    text = " ".join((i.get("failure_behaviour", "") + " " + i.get("endpoint_source", "")).lower() for i in http)
    assert "open" in text or "score 0" in text or "returns 0" in text, "say what happens when the scorer is down"


REQUIRED_ROLES = {
    "CLAIMS_ADMIN": "web.xml", "CLAIMS_USER": "web.xml", "CLAIMS_SUPERVISOR": "PaymentServlet.java",
    "AUDITOR": "claim.jsp", "CLAIMS-PAYMENTS": None, "REASSIGN_CLAIMS": "AdminServlet.java",
}


@pytest.mark.parametrize("role,where", sorted(REQUIRED_ROLES.items()))
def test_auth_check_found(role, where):
    hits = [a for a in INV["auth_checks"] if role in a["role"].upper()]
    assert hits, f"authorization check {role} missing"
    if where:
        assert any(where in ic.files_of(a) for a in hits), f"{role}: cite {where}"


def test_role_mechanisms():
    mech = {a["role"].upper(): a["mechanism"] for a in INV["auth_checks"]}
    assert mech.get("CLAIMS_SUPERVISOR") == "code"
    assert any("CLAIMS-PAYMENTS" in r and m == "filter" for r, m in mech.items())
    assert mech.get("REASSIGN_CLAIMS") == "database"


def test_scheduled_jobs():
    names = " ".join(j["name"].lower() for j in INV["scheduled_jobs"])
    assert "reinsurance" in names or "bordereau" in names
    assert "purge" in names
    purge = [j for j in INV["scheduled_jobs"] if "purge" in j["name"].lower()][0]
    assert purge["runs_in"] == "cron" and "crontab" in ic.files_of(purge)


@pytest.mark.parametrize("topic,needle", [
    ("timezone", "america/new_york"), ("charset", "iso-8859-1"), ("datasource", "java:/jdbc/claimdeskds"),
    ("database-vendor", "oracle"), ("filesystem", "/var/claimdesk"), ("app-server", "eap"), ("jdk", "8"),
])
def test_runtime_assumptions(topic, needle):
    hits = [r for r in INV["runtime_assumptions"] if r["topic"] == topic]
    assert hits, f"runtime assumption {topic} missing"
    assert any(needle in r["value"].lower() for r in hits), f"{topic}: value should mention {needle}"

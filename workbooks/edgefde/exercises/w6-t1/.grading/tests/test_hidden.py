"""Hidden checks for edgefde/w6-t1: one verified trust path for every client, no verification bypass."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import siteconf  # noqa: E402

BUNDLE = "/opt/corvane/certs/ca-bundle.pem"


def test_bundle_contents(tmp_path):
    b = siteconf.build_bundle(tmp_path)
    subs = siteconf.subjects(b)
    for need in ("Corvane Root CA G2", "Corvane Inspection Issuing CA 2", "ISRG Root X1"):
        assert any(need in s for s in subs), f"bundle lacks {need}"
    assert b.count("BEGIN CERTIFICATE") == b.count("END CERTIFICATE") >= 6


def test_bundle_pem_blocks_not_glued(tmp_path):
    b = siteconf.build_bundle(tmp_path)
    # each PEM block must end on its own line, or OpenSSL silently drops the next certificate
    assert "CERTIFICATE-----#" not in b and "CERTIFICATE----------BEGIN" not in b


def test_all_clients_point_at_one_bundle():
    e = siteconf.env()
    for k in ("REQUESTS_CA_BUNDLE", "SSL_CERT_FILE", "CURL_CA_BUNDLE"):
        assert e.get(k) == BUNDLE, f"{k}={e.get(k)}"
    assert siteconf.pip_conf().get("global", "cert") == BUNDLE
    if "PIP_CERT" in e:
        assert e["PIP_CERT"] == BUNDLE


def test_no_verification_bypass_anywhere():
    e = siteconf.env()
    for bad in ("PIP_TRUSTED_HOST", "UV_INSECURE_HOST", "PYTHONHTTPSVERIFY", "CURL_INSECURE", "UV_NATIVE_TLS_INSECURE"):
        assert bad not in e, bad
    c = siteconf.pip_conf()
    for sec in c.sections():
        assert not c.has_option(sec, "trusted-host"), f"pip.conf [{sec}] trusted-host"
    u = siteconf.uv_toml()
    assert "allow-insecure-host" not in u


@pytest.mark.parametrize("host", ["nexus.ops.corvane.internal", "pki.corvane.internal"])
def test_internal_hosts_bypass_proxy(host):
    entries = [x.strip() for x in siteconf.env()["NO_PROXY"].split(",") if x.strip()]
    assert "*" not in entries
    assert any(host == x or (x.startswith(".") and host.endswith(x)) or host.endswith("." + x) for x in entries), entries


def test_public_hosts_still_use_proxy():
    entries = [x.strip() for x in siteconf.env()["NO_PROXY"].split(",") if x.strip()]
    for host in ("telemetry.tessellate-edge.example", "pypi.org"):
        assert not any(host.endswith(x.lstrip(".")) for x in entries if x not in ("localhost", "127.0.0.1"))
    assert siteconf.env()["HTTPS_PROXY"] == "http://proxy.corvane.internal:3128"


def test_index_unchanged():
    assert siteconf.pip_conf().get("global", "index-url") == "https://nexus.ops.corvane.internal/repository/pypi-proxy/simple"
    assert siteconf.uv_toml()["index"][0]["url"] == "https://nexus.ops.corvane.internal/repository/pypi-proxy/simple"

import siteconf


def test_configs_parse():
    assert siteconf.env()["HTTPS_PROXY"].startswith("http://proxy.corvane.internal")
    assert siteconf.pip_conf().get("global", "index-url").startswith("https://")
    assert siteconf.uv_toml()["index"][0]["url"].startswith("https://")


def test_bundle_has_the_proxy_issuing_ca(tmp_path):
    subs = siteconf.subjects(siteconf.build_bundle(tmp_path))
    assert any("Corvane Inspection Issuing CA 2" in s for s in subs), subs

import json
import re
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

import yaml

EX = Path.cwd()
FX = EX / "tests" / "fixtures"


def gate(*files):
    return subprocess.run([sys.executable, str(EX / "scripts/check_image_arch.py"), *map(str, files)],
                          capture_output=True, text=True, timeout=30).returncode


def test_gate_multi_arch_ok():
    assert gate(FX / "index-multi.json") == 0


def test_gate_ignores_attestation_entries():
    assert gate(FX / "index-amd64-with-attestation.json") == 1


def test_gate_single_arm64_ok():
    assert gate(FX / "manifest-single.json", FX / "config-arm64.json") == 0


def test_gate_single_without_config_is_input_error():
    assert gate(FX / "manifest-single.json") == 2


def test_gate_garbage_is_input_error(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json")
    assert gate(p) == 2


def _job():
    return yaml.safe_load((EX / ".gitlab-ci.yml").read_text())["build-image"]


def test_build_produces_arm64():
    job = _job()
    script = " ".join(job.get("before_script", []) + job.get("script", []))
    native_arm = any("arm64" in t for t in job.get("tags", []))
    cross = re.search(r"buildx build[^\n]*--platform[ =]linux/arm64", script) and re.search(r"binfmt|qemu", script)
    assert native_arm or cross, "build on an ARM runner, or buildx --platform linux/arm64 with QEMU/binfmt"
    assert not re.search(r"--platform[ =][^ ]*amd64", script)


def test_no_latest_tag_pushed():
    text = (EX / ".gitlab-ci.yml").read_text()
    assert ":latest" not in text


def test_gate_job_gets_what_it_needs():
    ci = yaml.safe_load((EX / ".gitlab-ci.yml").read_text())
    gate_script = " ".join(ci["image-arch-gate"]["script"])
    assert "check_image_arch.py" in gate_script
    produced = set(ci["build-image"]["artifacts"]["paths"])
    used = set(re.findall(r"[\w.-]+\.json", gate_script))
    assert used <= produced, f"gate reads {used - produced} which build-image does not publish"
    assert ci["image-arch-gate"].get("allow_failure") is not True


def test_dockerfile_contract_kept():
    d = (EX / "Dockerfile").read_text()
    assert not re.search(r"--platform=\S*amd64", d)
    assert "EXPOSE 8080" in d and re.search(r"^USER\s+(?!root|0\b)", d, re.M)


def test_server_contract_guard():
    sys.path.insert(0, str(EX))
    from agent.server import serve
    srv = serve(0)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        port = srv.server_address[1]
        ping = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/ping", timeout=5).read())
        assert ping["status"] == "Healthy"
        req = urllib.request.Request(f"http://127.0.0.1:{port}/invocations", data=b'{"prompt":"hi"}', method="POST",
                                     headers={"Content-Type": "application/json"})
        assert "hi" in json.loads(urllib.request.urlopen(req, timeout=5).read())["result"]
    finally:
        srv.shutdown()


def test_answer_names_architecture():
    t = (EX / "ANSWER.md").read_text().lower()
    assert "arm64" in t and ("exec format" in t or "amd64" in t)

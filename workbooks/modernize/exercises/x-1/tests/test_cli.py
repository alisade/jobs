from pathlib import Path

import cli_lint

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = (ROOT / "config/migrate-security.cli").read_text()


def test_dry_run_is_clean():
    errs = cli_lint.lint(SCRIPT)
    assert not errs, "\n".join(errs)


def test_no_legacy_security_subsystem():
    assert "subsystem=security/" not in SCRIPT

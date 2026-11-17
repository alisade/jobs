import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def bundle(tmp_path_factory):
    out = tmp_path_factory.mktemp("bundle")
    _load("w1t1_generate", "scripts/generate.py").generate(out)
    return out


@pytest.fixture()
def imported(bundle, tmp_path):
    from keystone_import.importer import import_export
    db = tmp_path / "keystone.sqlite"
    import_export(bundle / "export", db)
    return bundle / "export", db

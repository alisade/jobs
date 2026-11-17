"""CLI: uv run python -m dvaccess <model.json> <user> <privilege> <record>"""

import sys

from . import SecurityModel, explain


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__)
        return 2
    path, user, privilege, record = argv
    model = SecurityModel.load(path)
    grants = explain(model, user, privilege, record)
    verdict = "ALLOWED" if grants else "DENIED"
    print(f"{verdict}: {user} {privilege} {record}")
    for g in grants:
        print(f"  - [{g.kind}] {g.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

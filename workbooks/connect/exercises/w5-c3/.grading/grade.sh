#!/usr/bin/env bash
# Grade connect/w5-c3: visible gates + hidden holdout gates (pristine simulator) in a temp copy.
# Last line of stdout: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
connect_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${connect_dir}/_env/grade-jest.sh" "${ex_dir}" 18 240

#!/usr/bin/env bash
# Grade awsfde/w2-t1: visible + hidden pytest checks (including the gateway replay) in a temp copy
# (the learner's folder is not written to). Last line: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-pytest.sh" "${ex_dir}" 15 240

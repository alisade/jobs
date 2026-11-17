#!/usr/bin/env bash
# Grade backend/w6-t1: visible + hidden pytest tests (offline Replayer + time-skipping env) in a temp
# copy. Last line: GRADE_TESTS {...}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track="$(cd "${ex_dir}/../.." && pwd)"
bash "${track}/_env/ensure-temporal.sh" >/dev/null || { echo "HARNESS ERROR: Temporal test server missing (cd ${track} && make deps)"; exit 2; }
exec bash "${track}/_env/grade-pytest.sh" "${ex_dir}" 11 300

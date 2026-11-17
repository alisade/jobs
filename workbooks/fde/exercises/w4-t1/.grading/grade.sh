#!/usr/bin/env bash
# Grade fde/w4-t1: visible + hidden tests in a temp copy (the learner's folder is not
# written to). Last line of stdout: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fde_dir="$(cd "${ex_dir}/../.." && pwd)"
if ! bash "${fde_dir}/_env/ensure-venv.sh" >&2; then
  echo "harness: could not build ${fde_dir}/.venv (see the message above)"
  exit 2
fi
exec "${fde_dir}/.venv/bin/python" "${fde_dir}/_env/run_tests.py" \
  --exercise "${ex_dir}" --expected-total 13 --timeout 240

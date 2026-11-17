#!/usr/bin/env bash
# Shared grader for Python exercises: builds/reuses audit/.venv, then runs visible tests/ plus
# hidden .grading/tests in a temp copy via run_tests.py. Last line: GRADE_TESTS {...}.
# Usage: grade-pytest.sh <ex_dir> <expected_total> [timeout_seconds]
set -u
ex_dir="${1:?ex_dir}"; expected="${2:-0}"; secs="${3:-240}"
env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
audit_dir="$(cd "${env_dir}/.." && pwd)"
if ! bash "${env_dir}/ensure-venv.sh" >&2; then
  echo "HARNESS ERROR: could not build ${audit_dir}/.venv (see above)"
  exit 2
fi
exec "${audit_dir}/.venv/bin/python" "${env_dir}/run_tests.py" --exercise "${ex_dir}" --expected-total "${expected}" --timeout "${secs}"

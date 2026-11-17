#!/usr/bin/env bash
# Shared grader for full-stack exercises (Python + TypeScript): runs grade-pytest.sh and
# grade-jest.sh on the same exercise, prints both reports, then one combined summary line:
#   GRADE_TESTS {"passed": N, "total": M}
# Usage: grade-mixed.sh <ex_dir> <py_expected_total> <js_expected_total> [timeout_seconds]
set -u
ex_dir="${1:?ex_dir}"; py_expected="${2:-0}"; js_expected="${3:-0}"; secs="${4:-240}"
env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
num() { printf '%s' "${1}" | sed -E "s/.*\"${2}\": ([0-9]+).*/\1/"; }
echo "== Python (pytest) =="
py_out="$(bash "${env_dir}/grade-pytest.sh" "${ex_dir}" "${py_expected}" "${secs}")"; py_rc=$?
printf '%s\n' "${py_out}" | sed '$d'
py_last="$(printf '%s\n' "${py_out}" | tail -1)"
echo "== TypeScript (jest) =="
js_out="$(bash "${env_dir}/grade-jest.sh" "${ex_dir}" "${js_expected}" "${secs}")"; js_rc=$?
printf '%s\n' "${js_out}" | sed '$d'
js_last="$(printf '%s\n' "${js_out}" | tail -1)"
case "${py_last}" in GRADE_TESTS*) ;; *) echo "HARNESS ERROR: pytest half did not report (exit ${py_rc})"; exit 2;; esac
case "${js_last}" in GRADE_TESTS*) ;; *) echo "HARNESS ERROR: jest half did not report (exit ${js_rc})"; exit 2;; esac
p=$(( $(num "${py_last}" passed) + $(num "${js_last}" passed) ))
t=$(( $(num "${py_last}" total) + $(num "${js_last}" total) ))
echo "combined: ${p}/${t} (python $(num "${py_last}" passed)/$(num "${py_last}" total), typescript $(num "${js_last}" passed)/$(num "${js_last}" total))"
echo "GRADE_TESTS {\"passed\": ${p}, \"total\": ${t}}"

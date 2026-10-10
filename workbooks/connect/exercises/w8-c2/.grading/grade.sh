#!/usr/bin/env bash
# Grade connect/w8-c2: compiles the project with JDK 21 and runs the learner's tests plus the hidden
# JUnit 5 tests in a temp copy. Last line: GRADE_TESTS {"passed": N, "total": M}.
# Needs JDK 21 + Maven; prints a clear HARNESS ERROR (exit 2) when they are missing.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
connect_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${connect_dir}/_env/grade-java.sh" "${ex_dir}" 13 300

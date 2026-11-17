#!/usr/bin/env bash
# Grade modernize/w1-c1: compiles with JDK 21 and runs the visible + hidden JUnit 5 tests in a temp
# copy. Last line: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-java.sh" "${ex_dir}" 12 300

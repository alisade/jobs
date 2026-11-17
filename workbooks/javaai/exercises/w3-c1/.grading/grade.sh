#!/usr/bin/env bash
# Grade javaai/w3-c1: visible + hidden JUnit 5 tests against a scripted Gemini fake, JDK 21.
# Last line: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-java.sh" "${ex_dir}" 17 300

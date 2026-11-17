#!/usr/bin/env bash
# Grade javaai/w1-c1: visible + hidden JUnit 5 tests (MockMvc, JdbcTemplate) in a temp copy, JDK 21.
# Last line: GRADE_TESTS {"passed": N, "total": M}. HARNESS ERROR (exit 2) if JDK/Maven are missing.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-java.sh" "${ex_dir}" 17 300

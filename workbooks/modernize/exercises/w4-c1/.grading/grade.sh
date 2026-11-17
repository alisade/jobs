#!/usr/bin/env bash
# Grade modernize/w4-c1: visible characterization tests + hidden Jakarta tests (embedded Tomcat) in a temp copy.
# Last line: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-java.sh" "${ex_dir}" 13 300

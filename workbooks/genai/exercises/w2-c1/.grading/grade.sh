#!/usr/bin/env bash
# Grade genai/w2-c1: pytest (service) + jest (TypeScript client) in temp copies.
# Last line of stdout: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-mixed.sh" "${ex_dir}" 18 9 240

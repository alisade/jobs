#!/usr/bin/env bash
# Grade modernize/w5-c1: builds a temp copy with the hidden tests added and runs dotnet test offline.
# Last line: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-dotnet.sh" "${ex_dir}" tests/PolicyPortal.Rating.Tests/PolicyPortal.Rating.Tests.csproj 300

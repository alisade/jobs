#!/usr/bin/env bash
# Shared grader for design (review-only) exercises. There are no automated tests: the rubric
# carries all 100 points and its automated row does not apply. This prints a completeness report
# for the grader (which template sections are still empty, word counts without the template's
# <!-- guidance --> comments, whether a diagram is present) and then the contract line
# GRADE_TESTS {"passed": 0, "total": 0}.
# Usage: grade-design.sh <ex_dir> [doc ...]   (default docs: DESIGN.md ANSWER.md)
set -u
ex_dir="${1:?ex_dir}"; shift || true
docs=("$@"); [ "${#docs[@]}" -eq 0 ] && docs=(DESIGN.md ANSWER.md)
echo "== design exercise: review-only, graded by rubric (no automated tests) =="
for d in "${docs[@]}"; do
  f="${ex_dir}/${d}"
  if [ ! -f "${f}" ]; then echo "MISSING  ${d}"; continue; fi
  python3 - "${f}" "${d}" <<'PY2'
import re, sys
path, name = sys.argv[1], sys.argv[2]
text = re.sub(r"(?s)<!--.*?-->", "", open(path, encoding="utf8", errors="replace").read())
print(f"-- {name}: {len(text.split())} words (template comments excluded)")
section, body = None, 0
def report():
    if section is not None:
        print(f"   {'filled' if body else 'EMPTY':8} {section}")
for line in text.splitlines():
    if line.startswith("## "):
        report(); section, body = line.strip(), 0
    elif section is not None and re.search(r"[A-Za-z0-9|]", line):
        body += 1
report()
diagram = re.search(r"```(mermaid|text)|\+--|-->|\|\s*->|->\s*\[", text)
print("   diagram: " + ("present" if diagram else "none found"))
PY2
done
echo "GRADE_TESTS {\"passed\": 0, \"total\": 0}"

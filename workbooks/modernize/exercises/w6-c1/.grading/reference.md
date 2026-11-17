# Reference: modernize/w6-c1

Model answers: `.grading/solution/skill/dependency-upgrade/SKILL.md`, `.grading/solution/DESIGN.md`,
`.grading/solution/ANSWER.md`. What a strong answer does:

- The skill measures before it changes, changes one thing per step, verifies after every step with commands that
  can fail, and stops for a human at major bumps, golden files, security config and shared public APIs. Its never
  list maps one-to-one onto the failure log, and its eval table includes refusals ("make CI green", "add --add-opens")
  and stops ("golden test fails after the change").
- The playbook starts with safety nets (characterization tests, enforcer, pr_guard, SBOM) before any upgrade, keeps
  JDK and Jakarta moves apart, dual-publishes corvane-commons before consumers move, and runs OIDC in shadow mode.
- Human gates are few and sharp; the review rubric is about agent failure modes, not style.
- The failure log is a feedback loop: every entry ends in a skill or harness change plus an eval case.

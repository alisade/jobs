# The pod

| Person | Level | Strengths | Watch-outs |
|---|---|---|---|
| You | lead | triage, incidents, agent workflows, verification | cannot review every line yourself; you own the gates |
| Priya | senior Java (12 y) | EAP, JPA/Hibernate, Maven | sceptical of agents; fast reviewer |
| Marcus | mid Java (5 y) | Spring, testing | has not used OpenRewrite; tends to accept agent output as is |
| Lena | mid (4 y), ex-.NET | security, OAuth, Okta admin | new to EAP |
| Tom | junior (1 y) | eager, good with agents | approved PR #1187 ("LGTM, CI green") |

Agents: Claude Code for every developer, headless runs in CI allowed with the
`dependency-upgrade` skill, read-only by default; write access only on a feature branch.

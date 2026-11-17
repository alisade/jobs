# Design: a reusable tenant-isolation kit for Tidewater Ask services

Author: <you>   Status: draft   Date: <date>

## 1. The pattern behind the three incidents
<!-- One paragraph per incident is not the point. What do they have in common (where the tenant came
from, where the check lived, what layer was missing)? State the failure pattern in two or three sentences. -->

## 2. Goals and non-goals
<!-- Measurable goals (e.g. every tenant-data path covered by X; time for a team to adopt; AppSec review
time). Non-goals: what this kit will not try to solve. -->

## 3. The kit: components
<!-- The reusable artifacts and what each guarantees. For example: a tenant-context library (TS and
Python) that is the only way to get a tenant; a CDK construct for tool Lambdas with ABAC session tags and
LeadingKeys; a Retrieve wrapper that cannot omit the filter; response defaults (no-store) and a CDN
behavior helper; a cross-tenant attack test kit; eval cases; a runbook. Say which are libraries, which
are constructs, which are tests. -->

## 4. API sketch
<!-- Concrete signatures in TypeScript and Python for the two or three most important pieces, and a CDK
usage example. Show what a team writes and what the kit does for them. -->

## 5. Defense in depth: which layer catches which bug
<!-- A table: each of the three incidents (and one you anticipate) against each layer (token claim,
library, IAM, data filter, edge, tests/evals). Where would each have been stopped? -->

## 6. Adoption and rollout
<!-- Order of adoption, how you get 14 teams there in a quarter, what is mandatory vs optional, how the
AppSec checklist changes, how you handle teams that cannot adopt yet. -->

## 7. How we know it works
<!-- Tests in CI (the attack kit), static checks (lint rules, cdk-nag style rules), runtime signals
(alarms on dropped foreign chunks, refused tenants), the evidence pack for customer vendor reviews. -->

## 8. What not to generalize
<!-- Things from the three fixes that should stay local, and why. Where a kit would cost more than it saves. -->

## 9. Risks and open questions
<!-- What could go wrong with the kit itself (a bug in the shared library is now a bug everywhere),
versioning, ownership. -->

## 10. The FDE story
<!-- How you would tell this in an interview in under two minutes: situation, the ambiguous ask, how you
narrowed it, the fix, the reusable pattern and its measured result. -->

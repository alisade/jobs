# Engagement note 3: Corvid Logistics (2026-11-12), embed URL served from the CDN cache

FDE remote: one engineer, one day.

- Symptom: embedded Quick Sight dashboards blank on refresh; one Corvid user saw Acme's numbers.
- Cause: the embed-URL endpoint moved under a CloudFront behavior whose cache policy had DefaultTTL
  300 and no identity in the cache key; the Lambda sent no Cache-Control, so a single-use embed URL was
  cached and served to everyone for five minutes.
- One-off fix: a /api/analytics/* behavior on Managed-CachingDisabled plus cache-control: no-store in
  the Lambda (TypeScript, CDK in TypeScript).
- Left behind: nothing reusable. The web team asked "which of our other API paths are authenticated
  and cached?"; nobody could answer.

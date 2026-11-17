# Engagement note 1: Delta Outfitters (2026-11-12), KB results from another tenant

FDE on site: one engineer, two days.

- Symptom: a newly onboarded tenant with three documents saw answers citing Acme Foods documents.
- Cause: a "fewer I-don't-know answers" change retried Bedrock Knowledge Base Retrieve WITHOUT the
  tenant_id metadata filter when the filtered call returned nothing above the score floor.
- One-off fix: removed the fallback in ask_service/retrieval.py; added a check that drops chunks whose
  tenant_id metadata is not the caller's. Shipped as a hotfix the same day.
- Left behind: one unit test in the ask_service repo. Nothing else.
- Customer quote: "How do we know the other five services that call Retrieve do not have the same bug?"

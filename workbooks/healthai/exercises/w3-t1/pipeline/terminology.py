"""Code system URIs used across the pipeline (shared module, introduced in release 2026.11.1)."""

ICD10 = "http://hl7.org/fhir/sid/icd-10"          # WHO ICD-10 (international, not used for US claims)
ICD10CM = "http://hl7.org/fhir/sid/icd-10-cm"     # ICD-10-CM (US diagnoses, HIPAA code set)
ICD10PCS = "http://www.cms.gov/Medicare/Coding/ICD10"  # ICD-10-PCS (inpatient procedures)
HCPCS = "https://www.cms.gov/Medicare/Coding/HCPCSReleaseCodeSets"
NPI = "http://hl7.org/fhir/sid/us-npi"

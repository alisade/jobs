# Release 2026.11.1 (deployed 2026-11-17 18:00 ET)

- PA-2211 Show payer name on determination letters (validator warns when Coverage.payor display is empty).
- PA-2230 Move code system URIs into the shared `pipeline/terminology.py` module (no behaviour change intended).
- PA-2234 Upgrade structlog 24.4 -> 25.1.

## Diff excerpt (PA-2230)

```
--- a/pipeline/mapper.py
+++ b/pipeline/mapper.py
-ICD10_SYSTEM = "http://hl7.org/fhir/sid/icd-10-cm"
+from . import terminology as T
 ...
-            "code": {"coding": [{"system": ICD10_SYSTEM, "code": icd_display_code(code)}]}}})
+            "code": {"coding": [{"system": T.ICD10, "code": icd_display_code(code)}]}}})

--- a/pipeline/criteria_engine.py
+++ b/pipeline/criteria_engine.py
-CM = "http://hl7.org/fhir/sid/icd-10-cm"
+from . import terminology as T
 ...
-            out += [c["code"] for c in r["code"]["coding"] if c.get("system") == CM]
+            out += [c["code"] for c in r["code"]["coding"] if c.get("system") == T.ICD10CM]
```

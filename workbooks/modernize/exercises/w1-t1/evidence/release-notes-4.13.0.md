# claimdesk-intake 4.13.0 (deployed 2026-11-11)

- CLM-4410: build and run on JDK 21 (was JDK 8). Launcher JAVA_HOME switched on cdk-batch-03.
- CLM-4398: claim.opened event schema v3 (adds lossDate as ISO-8601 date). Needs the Jackson
  java.time module; bumped jackson-databind and added jackson-datatype-jsr310 2.17.2.
- CLM-4402: regulatory audit fingerprint per FNOL (canonical JSON, SHA-256) to audit.csv.
- No other dependency changes.

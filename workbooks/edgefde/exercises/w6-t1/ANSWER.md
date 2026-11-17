# ANSWER: edgefde/w6-t1 pip and uv fail behind a TLS-inspecting proxy

## Approach

<!-- Which evidence you read in which order, and what each s_client capture told you. -->

## Root cause

<!-- Per client: pip before CHG-4471, uv, uplink client, model pull. Quote the evidence. Why
trusted-host made pip work and why that is not a fix. -->

## Fix

<!-- The bundle, the env, pip and uv configuration. Verification commands plant IT should run
(openssl s_client -CAfile, curl -v, pip download, uv sync, python -c "import requests; ..."). -->

## Trade-offs / what I would do in production

<!-- Bundle maintenance when the corporate CA rotates, certifi in venvs, uv native-tls vs SSL_CERT_FILE,
how this goes into the site readiness checklist. Short. -->

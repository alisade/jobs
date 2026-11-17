# edgefde/w6-t1 - pip and uv fail on the plant build box behind a TLS-inspecting proxy

**Type:** troubleshooting (configuration and evidence bundle) | **Estimate:** 1.5 hours | **Study plan:** Week 6 (Wed: locked-down networks, proxies and CA bundles)

## Scenario

You are installing the Tessellate Edge kit on `ops-build-02`, Corvane's level 3 build box at the
Dunmore plant (fictional). Plant IT sends you this:

> "pip was failing with SSL errors, so J. Ortiz added trusted hosts last Friday (CHG-4471) and pip
> works now. But uv in CI still fails on the edge-kit-cli download, the kit's uplink client cannot
> send features, and model downloads fail. Security says the trusted-host change must be reverted by
> Friday. We gave you the corporate root CA, what else do you need?"

You cannot reach the box from here; plant IT collected the evidence in `incident/` and gave you the
configuration files in `site/` and the CA files they published in `certs/`. Your job is to find the
real cause and hand back configuration that works with verification ON for every client (pip, uv,
requests, curl).

## What you have

| Path | What it is |
|---|---|
| `incident/` | pip, uv and client logs, `openssl s_client` captures, env, proxy policy, the change record (from `make setup`) |
| `site/proxy.env` | the profile script every shell and CI job sources (edit) |
| `site/pip.conf`, `site/uv.toml` | pip and uv configuration (edit) |
| `site/build-ca-bundle.sh` | assembles `/opt/corvane/certs/ca-bundle.pem` (edit) |
| `certs/` | PEM files from `http://pki.corvane.internal/` and the OS public roots (fixtures: the `# Subject:` comment lines describe each certificate) |

## Your task

1. Explain from the evidence why each client fails (pip before CHG-4471, uv, the uplink client, the
   model pull), quoting the lines that prove it.
2. Fix `site/`: one CA bundle, built by the script, that every client uses; no verification bypass
   anywhere; internal hosts not sent through the inspecting proxy.
3. Write the verification steps plant IT should run after applying it, and the revert of CHG-4471.

## Acceptance criteria (what the grader checks)

- `build-ca-bundle.sh` produces a bundle with the public roots, Corvane Root CA G2 and the proxy's
  issuing CA, with each PEM block on its own lines.
- `REQUESTS_CA_BUNDLE`, `SSL_CERT_FILE`, `CURL_CA_BUNDLE` and pip's `cert` all point at
  `/opt/corvane/certs/ca-bundle.pem`.
- No `trusted-host`, `PIP_TRUSTED_HOST`, `allow-insecure-host` or similar bypass remains.
- `NO_PROXY` covers `*.corvane.internal` with valid syntax and no `*`; public hosts still use the proxy.
- `ANSWER.md`: the root cause per client with evidence, why trusted-host "worked" for pip only, and the
  verification plan.

## How to run

```bash
make setup     # venv + incident/
make bundle    # run your bundle script against certs/
make test      # visible checks
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/w6-t1
make clean
```

## What to submit

Your changes under `site/` and a filled-in `ANSWER.md`.

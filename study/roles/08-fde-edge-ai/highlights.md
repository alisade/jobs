# Role 8: Forward Deployed Engineer (Edge AI, EE background preferred): highlights

The posting is in [posting.md](posting.md). The full material list with links is in [details.md](details.md).

This role is a field engineering job with an Edge AI flavor. The customer-facing half (embed with client
teams, frame the problem, debug on-site, leave reusable assets behind) is close to what you already do.
The technical half asks for things you have not done as a software engineer: production Python data
pipelines, MLOps, Edge AI model deployment, and some signal processing.

From the shared core you need [section 2](../../shared/details.md#2-agent-design-patterns-and-context-engineering)
(agent patterns), [section 3](../../shared/details.md#3-tool-calling-and-structured-outputs) (tool calling and
Pydantic contracts), [section 5](../../shared/details.md#5-verification-and-evals) (verification and evals) and
[section 6](../../shared/details.md#6-llm-security) (LLM security). Sections 1 and 4 help if you have time.
Skip section 8 (Gemini) unless the client runs on Google. For FDE storytelling, also read
[role 4 section 9](../04-aws-fde-agentic-ai/details.md#9-fde-skills-diagnosis-with-the-customer-then-reusable-patterns);
this track does not repeat it.

## Where you start

| Posting asks for | You already have |
|---|---|
| Embed on-site with clients, partner across BUs | Years embedded with federal (GSA) and mortgage-servicing (Lakeview) client teams, debugging their live environments with them. Remote and embedded, not travel-based on-site work |
| Frame customer problems and own the architecture | You design and own CDK stacks, Terraform/Spacelift stacks, chart release and ArgoCD paths for client teams |
| Comfort deploying and debugging on-site in complex enterprise environments | 26 years of P1s across AWS, Azure, Kubernetes, Jenkins, AD/LDAP, Linux and Windows, inside locked-down federal and financial networks |
| Reusable, customer-owned assets | Runbooks, CDK constructs, Helm charts, CI pipelines, hooks and skills that stay with the client team |
| Rapid iteration, measurable outcomes | Incident work where the result is measured: the error rate drops, the job runs, the deploy goes green |
| Custom data pipelines | Kinesis/Firehose streaming pipelines into S3 Tables, built as infrastructure (CDK). Not yet as Python application code |
| API integrations | Lambda and Step Functions integrations, SDK calls with retries, webhook and SNS wiring, MCP servers you run daily |
| MLOps/AI workflows | AI workflows: a daily Claude Code harness with skills, hooks and MCP servers. MLOps (registry, serving, drift): no |
| LLM/agentic systems (preferred) | Daily agentic tooling with guardrails, approval gates and permission scoping |
| Strong Python, 10+ years building production software | 26 years writing automation in TypeScript, bash and some Python. Production Python as the main language: not yet |
| Edge AI, signal processing, EE (preferred) | Not on record |
| Prior forward-deployed, field, or solutions engineering (preferred) | Yes: embedded client delivery is your day job. Frame it that way |

## Honest fit note

- **"EE background preferred" is in the job title, not just the preferred list.** That usually means the
  client work involves sensors, hardware, or signals (vibration, audio, RF, cameras, power). You do not
  have an EE degree or signal-processing work on record, and you should not imply one. A recruiter may
  filter on it.
- **What to do about it.** Ask the recruiter two questions before investing weeks: "Is EE a hard screen or
  a tie-breaker?" and "What do the Edge AI teams actually deploy: vision on cameras, audio or vibration
  on industrial machines, something else, and on what hardware?" If the answer is vision on NVIDIA
  Jetson, weight DeepStream and TensorRT. If it is industrial sensors, weight the signal-processing and
  time-series work. Either way, close the gap with a portfolio that shows you can handle signals as a
  software engineer: sampling, FFT, filtering and feature extraction in NumPy/SciPy, on a public
  industrial dataset, with measured results. That is not an EE degree, and you should say so, but it
  answers the practical question "can this person work with our sensor data?".
- **Your strongest card is the FDE half.** Most candidates with an EE or ML background have never sat with
  a client team in a locked-down network at 2 a.m. and found the real cause. You have. Lead with that, and
  tell it as outcomes: problem, constraint, what you built, what got measurably better, what the client
  kept.
- **"Strong Python" is required, not preferred.** Your Python is "some". Treat this as the first gap, not
  the last; every other technical item in the posting is delivered in Python.
- **Travel.** The posting expects travel and on-site embedding. Your embedded work has been remote or with
  local teams. Decide how much travel you will accept before the first call, and say it plainly.

## Gaps, most important first

1. **Production Python.** Packaging, typing, tests, async I/O, structured logging; Python as the main
   language of a shipped service, not a helper script.
2. **MLOps.** Model registry, versioned artifacts, serving, monitoring and drift, and CI that gates model
   promotion on eval metrics.
3. **Edge AI deployment.** ONNX export, quantization, ONNX Runtime, and one hardware stack (TensorRT on
   Jetson, or OpenVINO on Intel), measured for latency, size and accuracy.
4. **Signal processing basics and sensor data.** Sampling, Nyquist, aliasing, FFT, windowing, filters,
   spectral features, time-series storage. This is the EE filter.
5. **Data pipelines as application code.** Kafka (or MQTT) consumers and producers in Python, idempotency,
   backfills, schema evolution and data quality checks. The infra side transfers; the code does not yet.
6. **Edge fleet operations.** OTA rollout with canary and rollback, offline buffering and replay, device
   identity. Close to your CD and fleet work, but on devices instead of clusters.
7. **LLM/agentic systems at the edge.** Small models with llama.cpp or Ollama, tool calling on local
   models, hybrid edge-cloud routing.
8. **Field stories told as outcomes.** You have the experience; you need five crisp, numbered stories.

## Six-week plan

| Week | Focus | Output |
|---|---|---|
| 1 | Production Python and data pipelines: uv, ruff, mypy, pytest, Pydantic; a Kafka or MQTT ingest service with idempotent writes and a backfill command | An ingest service with tests, a replay/backfill CLI, and data quality checks that fail loudly |
| 2 | Signal processing: sampling, Nyquist, FFT, windowing, Welch PSD, Butterworth filters, on the CWRU bearing or MIMII dataset | A feature module (band energies, RMS, kurtosis, spectral peaks) with unit tests on synthetic signals of known frequency |
| 3 | MLOps: train a small anomaly model, MLflow tracking and registry, eval gate in GitHub Actions | A CI job that promotes a model version only if recall and false-alarm rate beat the current one |
| 4 | Edge AI: export to ONNX, quantize to INT8, run with ONNX Runtime on a Raspberry Pi, Jetson or an ARM64 container; optional TensorRT or OpenVINO | A benchmark table: FP32 vs INT8 size, latency p50/p95 and accuracy on device |
| 5 | Edge fleet: OTA rollout to 5-10 simulated devices with canary and rollback, offline buffering with idempotent replay; air-gapped install drill | A rollout runbook, a recorded canary failure with automatic rollback, and an install that works with no internet |
| 6 | Edge LLM agent plus the FDE write-up: local model with read-only tools over the pipeline data, cloud fallback; engagement report and handoff pack | The finished portfolio repo below, plus five field stories for interviews |

## Portfolio project: an edge-to-cloud machine-health kit, written up as an FDE engagement

Frame it as a client engagement from the first commit. The README opens with a one-page brief: "a plant
operator wants early warning of bearing failure on 10 machines, with a site network that blocks most
outbound traffic". State the baseline (time-based maintenance, no early warning) and the targets.

- **Data:** a public industrial dataset (CWRU bearing or MIMII machine sounds) replayed as live sensor
  streams over MQTT or Kafka, plus a simulator for injecting new faults. Real data makes the metrics mean
  something; simulation alone does not.
- **Pipeline (Python):** ingest with schema validation, windowing, FFT feature extraction with SciPy,
  idempotent writes keyed by device and window, a backfill command, and data quality checks.
- **Model:** a small anomaly detector, trained and tracked in MLflow, exported to ONNX and quantized to
  INT8. A CI job gates promotion in the registry on recall and false-alarm rate against the current
  champion.
- **Edge:** ONNX Runtime on a Raspberry Pi or Jetson (or an ARM64 container emulating one). The device
  sends features and alerts, not raw audio, and buffers to SQLite when the uplink is down, then replays
  without duplicates.
- **Fleet:** OTA rollout to a small simulated fleet: canary one device, check health and model metrics,
  promote or roll back automatically. Every device reports its model version.
- **Agent:** an operator assistant that explains an anomaly ("why did machine 4 alert?") using read-only
  tool calls over the feature store, the alert log and the model card. It runs on a local small model
  with an optional cloud model for harder questions, and it cannot change device or model state.
- **Locked-down mode:** the whole kit installs from a wheelhouse and saved container images, with a
  corporate proxy and a custom CA bundle, and no other internet access.
- **Measured outcome:** detection recall and false alarms per machine-week, lead time before failure,
  model size and on-device latency FP32 vs INT8, bandwidth saved by sending features, and rollout time
  for the fleet.
- **Customer-owned handoff:** model card, runbook (retrain, roll back, add a device), architecture
  diagram, an eval suite the client can rerun, and a short "what we would do next" note.

Do not include any GSA or Lakeview specifics.

## One-line pitch

"I have spent 26 years embedded with client teams inside locked-down enterprise networks, finding the real
cause and leaving them with systems they own; I now build the edge-to-cloud ML and agent pipelines that
sit on top, in Python, with measured results."

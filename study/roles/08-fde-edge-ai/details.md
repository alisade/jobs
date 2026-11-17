# Role 8: Forward Deployed Engineer (Edge AI, EE background preferred): details

Material for each item in [highlights.md](highlights.md). Every topic has the same parts: why it matters,
what you already have (only where it is true), what to learn, links, and an exercise. All links were
checked on 2026-11-13.

Agent design, tool calling, evals and LLM security are in the [shared core](../../shared/details.md) and
are not repeated here. Section numbers below are this track's own.

---

## 1. FDE practice: framing, ownership, field iteration, customer-owned assets

**Why:** "Frame customer problems and own the architecture that solves them", "Drive rapid iteration and
field learning to deliver measurable customer outcomes", and "Produce reusable, customer-owned assets that
create defensible wedges".

**You already have:** years embedded with GSA and Lakeview client teams, debugging live environments with
them and leaving runbooks, constructs, pipelines and hooks behind. The diagnosis-in-front-of-the-customer
skills are covered in [role 4 section 9](../04-aws-fde-agentic-ai/details.md#9-fde-skills-diagnosis-with-the-customer-then-reusable-patterns).

**Learn:**
- Problem framing: who has the problem, what it costs them today (downtime hours, false alarms, manual
  inspections), what "working" means as a number, and what is out of scope. Write it as a one-page brief
  before writing code.
- Talking to users without leading them: ask about what they did last time, not what they would like.
- Owning the architecture: the decision record (options, trade-off, why), the constraints you were given
  (network, hardware, data access, security review), and who operates it after you leave.
- Field iteration: ship a thin end-to-end slice in the first week, measure it against the baseline, then
  widen. A notebook that works on a laptop is not a delivery.
- Measurable outcomes: agree the metric and the baseline before the work starts, so the result is not
  argued about later.
- Customer-owned assets: code in their repo, runbooks in their wiki, evals they can rerun, a model card,
  a handoff session. "Defensible wedge" is the business side: an asset that solves the first problem well
  makes the next engagement with that client easier. Read the a16z piece to understand how vendors think
  about it, so you can talk to it in an interview.
- What a forward-deployed engineer is in current industry use: a software engineer who works inside the
  customer's environment and builds for that customer, as opposed to a solutions engineer who mostly
  demos. Palantir coined the role; its own blog posts on it are behind a bot wall and are not linked here.

**Links:**
- [What are Forward Deployed Engineers, and why are they so in demand? (The Pragmatic Engineer)](https://newsletter.pragmaticengineer.com/p/forward-deployed-engineers)
- [Trading margin for moat: why the Forward Deployed Engineer is the hottest job in startups (a16z)](https://a16z.com/services-led-growth/)
- [The Mom Test (customer conversations)](https://www.momtestbook.com/)
- [Postmortem culture (Google SRE book)](https://sre.google/sre-book/postmortem-culture/)
- [Effective troubleshooting (Google SRE book)](https://sre.google/sre-book/effective-troubleshooting/)

**Exercise:** Write the one-page engagement brief for the portfolio project before any code: user,
problem, current cost, baseline, target metric, constraints, out of scope, and the handoff list. Then
rewrite three of your own client stories in the same shape, each ending with a number and an asset the
client kept.

---

## 2. Production Python

**Why:** "Strong Python plus experience with data pipelines, APIs, and MLOps/AI workflows" and "Write
production-grade code". Everything else in this track is delivered in Python.

**You already have:** some Python for ops work, and production discipline from TypeScript CDK (types,
tests, CI).

**Learn:**
- Project layout with `pyproject.toml` and uv, a lock file, and reproducible installs.
- Type hints checked by mypy in CI; ruff for lint and format.
- pytest: fixtures, parametrize, temporary directories, and property-based tests with Hypothesis for
  parsers and signal functions.
- Pydantic models at every boundary (messages, API payloads, config), and settings from env with
  pydantic-settings.
- asyncio for I/O-bound services (consumers, HTTP clients), and when a plain thread or process pool is
  simpler.
- Structured logging and OpenTelemetry traces and metrics from Python.
- Packaging a service as a wheel and a container image for both amd64 and arm64.

**Links:**
- [Python Packaging User Guide](https://packaging.python.org/en/latest/)
- [uv](https://docs.astral.sh/uv/)
- [Ruff](https://docs.astral.sh/ruff/)
- [mypy](https://mypy.readthedocs.io/en/stable/)
- [pytest](https://docs.pytest.org/en/stable/)
- [Hypothesis](https://hypothesis.readthedocs.io/en/latest/)
- [pydantic-settings](https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/)
- [asyncio](https://docs.python.org/3/library/asyncio.html)
- [Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [OpenTelemetry for Python](https://opentelemetry.io/docs/languages/python/)
- [Docker multi-platform builds](https://docs.docker.com/build/building/multi-platform/)

**Exercise:** Set up the portfolio repo skeleton: uv project, ruff, mypy strict on the `src/` package,
pytest with coverage, a GitHub Actions job that runs all of them, and a multi-arch image build. Nothing
merges unless all checks pass.

---

## 3. Data pipelines in production: batch and streaming

**Why:** "Write production-grade code: custom data pipelines". Edge AI clients produce continuous sensor
streams and also need historical reprocessing.

**You already have:** Kinesis/Firehose streaming pipelines into S3 Tables, built as infrastructure. You
know partitions, retention, delivery retries and the cost of reprocessing from the infra side.

**Learn:**
- Kafka basics as a client author: topics, partitions, keys, consumer groups, offsets, rebalances.
  Commit offsets after the write succeeds, not before.
- Delivery semantics: at-most-once, at-least-once, exactly-once. In practice: at-least-once delivery plus
  idempotent writes keyed on a natural ID (device, timestamp window).
- Idempotent producer settings and transactions, and why they do not make your downstream database
  idempotent.
- Schemas and evolution: a schema registry, compatible changes, versioned Pydantic models.
- Batch with an orchestrator (Airflow or Dagster): partitions by time, reruns, and backfills that do not
  double-count.
- Columnar data: Parquet through Arrow, Polars for fast dataframes, table formats like Iceberg for
  reprocessing history.
- Data quality: schema checks, ranges, null rates, freshness and volume checks; fail the run or quarantine
  the batch, never pass bad data silently.
- MQTT for device-side messaging (QoS levels, retained messages, a broker such as Mosquitto) and bridging
  it into Kafka or a cloud stream.

**Links:**
- [Apache Kafka documentation](https://kafka.apache.org/documentation/)
- [Kafka producer config: enable.idempotence](https://kafka.apache.org/documentation/#producerconfigs_enable.idempotence)
- [Message delivery semantics (Confluent)](https://docs.confluent.io/kafka/design/delivery-semantics.html)
- [Exactly-once semantics in Kafka (Confluent)](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/)
- [Confluent Python client](https://docs.confluent.io/kafka-clients/python/current/overview.html)
- [Schema Registry overview](https://docs.confluent.io/platform/current/schema-registry/index.html)
- [Quix Streams (Python stream processing on Kafka)](https://quix.io/docs/quix-streams/introduction.html)
- [Airflow DAG runs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html)
- [Airflow backfill](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/backfill.html)
- [Dagster docs](https://dagster.io/docs)
- [Apache Arrow for Python](https://arrow.apache.org/docs/python/index.html)
- [Polars](https://docs.pola.rs/)
- [Apache Iceberg](https://iceberg.apache.org/docs/latest/)
- [Pandera (dataframe validation)](https://pandera.readthedocs.io/en/stable/)
- [Great Expectations](https://docs.greatexpectations.io/docs/home/)
- [MQTT](https://mqtt.org/)
- [Eclipse Mosquitto](https://mosquitto.org/)
- [Paho MQTT Python client](https://eclipse.dev/paho/files/paho.mqtt.python/html/index.html)

**Exercise:** Build the ingest service: devices publish to MQTT, a bridge forwards to Kafka, a Python
consumer validates, windows and writes features to Parquet keyed by (device, window start). Kill the
consumer mid-batch and restart it; show the row count is unchanged. Then run a backfill over one past day
twice and show no duplicates. Add three data quality checks that fail the run.

---

## 4. API integrations

**Why:** "Write production-grade code: ... API integrations". In the field this means the client's
historian, CMMS or ticketing system, a cloud API, and your own service API.

**You already have:** Lambda and Step Functions integrations, SDK calls with retries, SNS and webhook
wiring, and day-to-day use of MCP servers over Jira, Spacelift and AWS.

**Learn:**
- HTTP clients in Python with httpx: timeouts on every call, connection pools, async.
- Retries with exponential backoff and jitter, only on retryable errors, with a retry budget.
- Idempotency keys for writes, so a retry never creates a second work order.
- Pagination, rate limits (429 and Retry-After), and partial failure in batch calls.
- Auth patterns: OAuth client credentials, API keys from a secret store, mTLS.
- Contracts: OpenAPI specs, Pydantic models generated from or checked against them, contract tests with
  recorded responses.
- Serving your own API with FastAPI (see [shared section 3](../../shared/details.md#3-tool-calling-and-structured-outputs)
  for Pydantic contracts).

**Links:**
- [HTTPX](https://www.python-httpx.org/)
- [Tenacity (retries)](https://tenacity.readthedocs.io/en/latest/)
- [Timeouts, retries, and backoff with jitter (Amazon Builders' Library)](https://builder.aws.com/content/3EumjoZascWd1oZiEgL8ORlv3qE/timeouts-retries-and-backoff-with-jitter)
- [Making retries safe with idempotent APIs (Amazon Builders' Library)](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- [Idempotent requests (Stripe API)](https://docs.stripe.com/api/idempotent_requests)
- [OpenAPI specification](https://spec.openapis.org/oas/latest.html)

**Exercise:** Write a client for a mock maintenance-ticket API (FastAPI) that raises a work order when an
anomaly is confirmed. Make the mock fail 30% of calls with 500 or 429. Show that the client retries with
backoff, honors Retry-After, and never creates a duplicate work order thanks to an idempotency key.

---

## 5. MLOps: registry, serving, monitoring, CI for models

**Why:** "MLOps/AI workflows" appears in both the responsibilities and the required qualifications.

**You already have:** CI/CD, artifact versioning, promotion between environments, approval gates and
observability. MLOps is that discipline applied to models and data; the new parts are the ML-specific
failure modes.

**Learn:**
- Experiment tracking: parameters, metrics, artifacts, the data version used for training.
- Model registry: versions, aliases (champion and challenger), lineage back to the run and the data.
- Model packaging: MLflow model format, signatures, and ONNX as the edge format (section 7).
- Serving options: batch scoring, a REST endpoint (MLflow serving, KServe, Triton), and on-device.
- CI for models: an eval suite on a fixed holdout set, gates on metrics (recall, false-alarm rate,
  latency), and promotion only when the challenger beats the champion. Same idea as eval gates in
  [shared section 5](../../shared/details.md#5-verification-and-evals).
- Monitoring: input drift, prediction drift, and the metric that matters once labels arrive (confirmed
  failures). Drift is a signal to investigate, not an automatic retrain.
- Data versioning with DVC or table snapshots, so any model can be rebuilt.
- ML technical debt: the pipeline around the model is most of the system.

**Links:**
- [MLflow docs](https://mlflow.org/docs/latest/)
- [MLflow Model Registry](https://mlflow.org/docs/latest/ml/model-registry/)
- [MLflow Models](https://www.mlflow.org/docs/latest/ml/model/)
- [MLflow model evaluation](https://mlflow.org/docs/latest/ml/evaluation/)
- [MLflow deployment](https://mlflow.org/docs/latest/ml/deployment/)
- [MLOps: continuous delivery and automation pipelines in ML (Google Cloud)](https://docs.cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning)
- [Continuous delivery for machine learning (martinfowler.com)](https://martinfowler.com/articles/cd4ml.html)
- [Rules of Machine Learning (Google)](https://developers.google.com/machine-learning/guides/rules-of-ml)
- [Hidden technical debt in machine learning systems (NeurIPS 2015)](https://papers.nips.cc/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html)
- [KServe](https://kserve.github.io/website/)
- [NVIDIA Triton Inference Server](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/index.html)
- [Evidently (drift and model monitoring)](https://docs.evidentlyai.com/introduction)
- [DVC](https://doc.dvc.org/)
- [CML (CI for ML)](https://cml.dev/)

**Exercise:** Train two anomaly models (an IsolationForest baseline and a small neural net) on the
section 6 features. Log both in MLflow, register them, and write a GitHub Actions job that evaluates a new
version on a fixed holdout set and moves the "champion" alias only if recall is higher and the false-alarm
rate is not worse. Post the comparison as a pull request comment. Then shift the input distribution in
the simulator and show a drift report flagging it.

---

## 6. Signal processing for a software engineer, and sensor data

**Why:** "EE background preferred" (in the title) and "Edge AI, LLM/agentic systems, or
signal-processing background" (preferred). Sensor clients will expect you to talk about sample rates and
spectra without hand-waving.

**Learn:**
- Sampling: sample rate, the Nyquist frequency (half the sample rate), aliasing, and why anti-aliasing
  happens before sampling, in hardware.
- The DFT and FFT: bins, frequency resolution (sample rate divided by window length), real FFT, magnitude
  and phase.
- Windowing (Hann, Hamming) and spectral leakage; overlapping windows; spectrograms (STFT).
- Power spectral density with Welch's method, which is how vibration data is usually summarized.
- Filters: low-pass, high-pass, band-pass; FIR vs IIR; Butterworth design; zero-phase filtering with
  `filtfilt` for offline work; why streaming filters need state.
- Time-domain features: RMS, peak, crest factor, kurtosis. Frequency-domain features: band energies,
  dominant frequencies, harmonics of a known shaft speed.
- Audio as a signal: mel spectrograms and MFCCs, the usual inputs for machine-sound models.
- Sensor data handling: timestamps and clock drift, gaps and resampling, units and calibration, storing
  time series (TimescaleDB, InfluxDB, or Parquet partitioned by time).
- Classical anomaly detection before deep learning: thresholds on features, IsolationForest, one-class
  methods.

**Links:**
- [SciPy signal processing tutorial](https://docs.scipy.org/doc/scipy/tutorial/signal.html)
- [SciPy FFT tutorial](https://docs.scipy.org/doc/scipy/tutorial/fft.html)
- [scipy.signal reference](https://docs.scipy.org/doc/scipy/reference/signal.html)
- [scipy.signal.welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html)
- [scipy.signal.butter](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.butter.html)
- [NumPy FFT routines](https://numpy.org/doc/stable/reference/routines.fft.html)
- [Nyquist-Shannon sampling theorem (Wikipedia)](https://en.wikipedia.org/wiki/Nyquist%E2%80%93Shannon_sampling_theorem)
- [Think DSP (free book, Python)](https://greenteapress.com/wp/think-dsp/)
- [Think DSP code and notebooks](https://github.com/AllenDowney/ThinkDSP)
- [The Scientist and Engineer's Guide to Digital Signal Processing (free book)](https://www.dspguide.com/)
- [librosa (audio analysis)](https://librosa.org/doc/latest/index.html)
- [CWRU Bearing Data Center](https://engineering.case.edu/bearingdatacenter)
- [MIMII dataset: sounds of malfunctioning industrial machines](https://zenodo.org/records/3384388)
- [scikit-learn novelty and outlier detection](https://scikit-learn.org/stable/modules/outlier_detection.html)
- [PyOD (outlier detection library)](https://pyod.readthedocs.io/en/latest/)
- [TimescaleDB docs (Tiger Data)](https://www.tigerdata.com/docs)
- [InfluxDB docs](https://docs.influxdata.com/)

**Exercise:** In a notebook, then as a tested module: generate a 120 Hz sine plus noise sampled at 1 kHz,
find the peak with an FFT, then sample the same signal at 200 Hz and show the alias at 80 Hz. Apply a
Butterworth band-pass and show the noise floor drop. Then load CWRU bearing data, compute Welch PSD and
time-domain features per one-second window, and plot healthy vs faulty. Write unit tests that feed
synthetic signals of known frequency and assert the features come out right.

---

## 7. Edge AI: model optimization and runtimes

**Why:** "Embed on-site with clients, partnering across BUs, and Edge AI teams" and "Edge AI" (preferred).
Edge AI teams care about model size, latency, power and accuracy on a specific device.

**Learn:**
- ONNX as the portable model format: export from PyTorch and scikit-learn, inspect the graph with Netron,
  check opset versions.
- ONNX Runtime: sessions, graph optimizations, threading, and execution providers (CPU, CUDA, TensorRT,
  OpenVINO) for the same model file.
- Quantization: dynamic vs static INT8, calibration data, per-channel weights, and measuring the accuracy
  drop. Always report size, latency and accuracy together.
- TensorRT on NVIDIA: building an engine from ONNX, FP16 and INT8 precision, engines tied to the GPU and
  TensorRT version they were built on.
- NVIDIA Jetson: JetPack, what runs on-device, and DeepStream for multi-camera video pipelines (the
  likely stack if the client does vision).
- OpenVINO on Intel CPUs, GPUs and NPUs, the other common industrial edge stack.
- LiteRT (formerly TensorFlow Lite) for microcontrollers and phones, so you recognize it.
- Benchmarking honestly: warm-up runs, p50 and p95 latency, batch size 1, thermal throttling on small
  boards.

**Links:**
- [ONNX](https://onnx.ai/)
- [ONNX Runtime docs](https://onnxruntime.ai/docs/)
- [ONNX Runtime with Python](https://onnxruntime.ai/docs/get-started/with-python.html)
- [ONNX Runtime quantization](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html)
- [ONNX Runtime graph optimizations](https://onnxruntime.ai/docs/performance/model-optimizations/graph-optimizations.html)
- [ONNX Runtime performance tuning](https://onnxruntime.ai/docs/performance/tune-performance/)
- [ONNX Runtime execution providers](https://onnxruntime.ai/docs/execution-providers/)
- [TensorRT execution provider](https://onnxruntime.ai/docs/execution-providers/TensorRT-ExecutionProvider.html)
- [OpenVINO execution provider](https://onnxruntime.ai/docs/execution-providers/OpenVINO-ExecutionProvider.html)
- [ONNX Runtime on IoT and edge](https://onnxruntime.ai/docs/tutorials/iot-edge/)
- [PyTorch ONNX export](https://docs.pytorch.org/docs/stable/onnx.html)
- [Export a PyTorch model to ONNX (tutorial)](https://docs.pytorch.org/tutorials/beginner/onnx/export_simple_model_to_onnx_tutorial.html)
- [sklearn-onnx](https://onnx.ai/sklearn-onnx/)
- [Netron (model viewer)](https://netron.app/)
- [TensorRT documentation](https://docs.nvidia.com/deeplearning/tensorrt/latest/index.html)
- [TensorRT quick start guide](https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/quick-start-guide.html)
- [NVIDIA JetPack](https://developer.nvidia.com/embedded/jetpack)
- [Jetson software documentation](https://docs.nvidia.com/jetson/)
- [DeepStream SDK developer guide](https://docs.nvidia.com/deepstream)
- [OpenVINO documentation](https://docs.openvino.ai/2026/index.html)
- [LiteRT (Google AI Edge)](https://developers.google.com/edge/litert)
- [Hugging Face Optimum ONNX](https://huggingface.co/docs/optimum-onnx/index)

**Exercise:** Export the section 5 neural model to ONNX, run it with ONNX Runtime on CPU, then quantize
it to INT8 (static, using 200 windows of calibration data). Produce one table: file size, p50/p95
latency at batch size 1, recall and false-alarm rate, for FP32 and INT8, on your laptop and on a
Raspberry Pi or an ARM64 container. If you can get a Jetson, add a TensorRT row; otherwise add an
OpenVINO row on an Intel CPU.

---

## 8. Edge deployment, fleet OTA and offline operation

**Why:** "Comfort deploying and debugging on-site" and the Edge AI team partnership. A model is not
delivered until it runs on every device and can be rolled back.

**You already have:** fleet thinking from Kubernetes and ArgoCD (versioned releases, canary, rollback,
drift between desired and live state), container builds and CI/CD. This maps closely; the differences
are bad networks, slow links, and devices you cannot SSH into easily.

**Learn:**
- Device identity and enrollment: per-device certificates, never shared keys.
- OTA approaches: full image updates with A/B partitions (Mender), container-based updates (balena,
  AWS IoT Greengrass components, Azure IoT Edge modules), or lightweight Kubernetes (k3s) on bigger
  devices.
- Separate the model from the application: ship a new model file without rebuilding the app, with the
  version reported back.
- Rollout strategy: canary one device, health and model-metric checks, phased rollout, automatic rollback.
- Offline operation: local inference keeps running without the cloud; buffer results locally (SQLite in
  WAL mode), replay idempotently when the link returns; cap disk use.
- Bandwidth: send features and alerts, not raw signals, unless a human asks for a raw clip.
- Air-gapped installs on devices: saved images, local registries, k3s air-gap install.

**Links:**
- [Mender documentation](https://docs.mender.io/)
- [Mender deployments](https://docs.mender.io/overview/deployment)
- [balena documentation](https://docs.balena.io/)
- [AWS IoT Greengrass V2](https://docs.aws.amazon.com/greengrass/v2/developerguide/what-is-iot-greengrass.html)
- [AWS IoT Jobs](https://docs.aws.amazon.com/iot/latest/developerguide/iot-jobs.html)
- [Azure IoT Edge](https://learn.microsoft.com/en-us/azure/iot-edge/about-iot-edge)
- [K3s](https://docs.k3s.io/)
- [K3s air-gap install](https://docs.k3s.io/installation/airgap)
- [SQLite write-ahead logging](https://www.sqlite.org/wal.html)
- [docker image save](https://docs.docker.com/reference/cli/docker/image/save/)

**Exercise:** Run 5-10 simulated devices (containers, or k3s nodes) that each pull a model version from a
manifest. Write a rollout controller: canary one device, wait for N windows of healthy metrics, then roll
out in batches. Ship a deliberately broken model and show the canary fails its check and rolls back
automatically. Cut the network to two devices for ten minutes and show they keep scoring, buffer locally,
and replay without duplicates afterwards.

---

## 9. LLM and agentic systems at the edge

**Why:** "Edge AI, LLM/agentic systems" (preferred) and "MLOps/AI workflows". Clients with weak or
restricted networks need language models that run locally, with the cloud as an option rather than a
dependency.

**You already have:** daily agentic tooling with tool calling, permission scoping and approval gates
(see the shared core for [agent patterns](../../shared/details.md#2-agent-design-patterns-and-context-engineering),
[tool calling](../../shared/details.md#3-tool-calling-and-structured-outputs) and
[LLM security](../../shared/details.md#6-llm-security)).

**Learn:**
- Local inference: llama.cpp (GGUF files, quantization levels such as Q4 and Q8, the built-in server) and
  Ollama (model pulls, the OpenAI-compatible API, tool calling).
- Small open models (for example Gemma) and what they can and cannot do: short tool-calling tasks and
  summaries yes, long multi-step reasoning less so.
- Hardware budgets: model size vs RAM, tokens per second on a Pi vs a Jetson vs a laptop. Jetson AI Lab
  has measured examples.
- Hybrid edge-cloud: route simple questions to the local model and hard ones to a cloud model when the
  link and policy allow; never send raw site data to the cloud without approval.
- Grounding the agent in pipeline data through read-only tools (feature store, alert log, model card),
  with structured outputs validated by Pydantic.
- Evals on the small model, the same way as on a cloud model, plus latency per answer on the device.

**Links:**
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [llama.cpp quantize tool](https://github.com/ggml-org/llama.cpp/blob/master/tools/quantize/README.md)
- [llama.cpp server](https://github.com/ggml-org/llama.cpp/tree/master/tools/server)
- [GGUF format (Hugging Face)](https://huggingface.co/docs/hub/gguf)
- [Ollama docs](https://docs.ollama.com/)
- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)
- [Ollama model library](https://ollama.com/library)
- [Gemma docs](https://ai.google.dev/gemma/docs)
- [Jetson AI Lab](https://www.jetson-ai-lab.com/)
- [Quantization overview (Hugging Face Transformers)](https://huggingface.co/docs/transformers/main/en/quantization/overview)

**Exercise:** Build the operator assistant: a local model under Ollama or llama.cpp with three read-only
tools (get alerts for a machine, get feature history for a window, get the model card). Ask it "why did
machine 4 alert at 14:05?" and require a Pydantic-validated answer that cites the tool results. Add a
router that sends a question to a cloud model only when a flag allows it. Run 15 eval cases on both the
local and the cloud path and record accuracy and latency per answer. Plant an instruction in an alert
note and show the tool scoping, not the model, prevents harm.

---

## 10. On-site debugging in locked-down enterprise networks

**Why:** "Comfort deploying and debugging on-site in complex enterprise environments" and "Embed on-site
with clients".

**You already have:** this is home ground. Federal and financial networks, proxies, AD/LDAP and Kerberos,
Windows and Linux, private endpoints, jump hosts, change control. What is new is doing it with a Python
and ML stack instead of infra tools, on a client laptop or device you do not control.

**Learn:**
- Corporate proxies for Python and containers: `HTTPS_PROXY`, `NO_PROXY`, the Docker daemon proxy, and
  curl's proxy flags for quick tests.
- TLS interception: clients that fail with "certificate verify failed" because a proxy re-signs traffic.
  Point pip, uv and requests at the corporate CA bundle instead of turning verification off.
- No internet at all: build a wheelhouse with `pip download` or a locked uv environment, save container
  images to tar files, mirror models (ONNX, GGUF) as files with checksums.
- Packet-level evidence: tcpdump and Wireshark to show the client's network team exactly where a
  connection stops.
- Working within change control: a written plan, a rollback, and the client's approval before touching
  their systems. You already work this way; say so in interviews.
- A field kit: a laptop setup and a USB drive with everything needed to install the stack offline.

**Links:**
- [pip: HTTPS certificates](https://pip.pypa.io/en/stable/topics/https-certificates/)
- [pip download](https://pip.pypa.io/en/stable/cli/pip_download/)
- [uv: TLS certificates](https://docs.astral.sh/uv/concepts/authentication/certificates/)
- [uv cache](https://docs.astral.sh/uv/concepts/cache/)
- [Requests: SSL certificate verification and proxies](https://requests.readthedocs.io/en/latest/user/advanced/)
- [Python ssl module](https://docs.python.org/3/library/ssl.html)
- [Docker daemon proxy configuration](https://docs.docker.com/engine/daemon/proxy/)
- [Everything curl: proxies](https://everything.curl.dev/usingcurl/proxies/)
- [tcpdump man page](https://www.tcpdump.org/manpages/tcpdump.1.html)
- [Wireshark documentation](https://www.wireshark.org/docs/)

**Exercise:** Run a "hostile site" drill on the portfolio kit: a VM or container network with no
internet except through a proxy that re-signs TLS with your own CA (mitmproxy or squid). Install and run
the whole kit there from a wheelhouse, saved images and mirrored model files. Write down each failure you
hit and the fix, and turn the list into a one-page "site readiness checklist" that ships with the
handoff pack.

---

## 11. Presenting the background

**Why:** "BS/MS in CS, EE, or related; 10+ years building production software" and "Prior
forward-deployed, field, or solutions-engineering experience" (preferred).

**Learn:**
- Lead with field delivery: embedded with client teams, owning architecture, debugging live systems,
  leaving assets the client kept. Use the word "embedded"; it is the posting's word.
- Call 26 years of infrastructure code and automation what it is: production software. Do not stretch it
  into "ML engineer".
- Show the new skills as the portfolio repo with numbers (latency, size, recall, rollout time), and say
  plainly that your Python, MLOps and Edge AI work is recent and portfolio-based.
- On EE: say you do not have an EE degree or a signal-processing job behind you, and point at section 6
  work as what you can do with signals today.
- Recruiter questions to ask: is EE a screen or a tie-breaker; what the Edge AI teams deploy and on what
  hardware; how much travel, and for how long per visit; whether the client sites are air-gapped.

**Exercise:** Rewrite the top third of your resume for this posting: four bullets on embedded client
delivery with numbers, two on pipelines and integrations, and one line pointing at the portfolio repo.
Practise a two-minute walkthrough of the portfolio framed as an engagement: problem, constraint,
architecture, result, handoff.

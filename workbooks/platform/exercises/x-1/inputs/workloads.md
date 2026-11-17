# Workload classes on the prod clusters

| Class | Examples | Replicas | PDB today | Graceful shutdown | Notes |
|---|---|---|---|---|---|
| Stateless API | riq-api, mdm-api, rdm-api | 6-12 per cluster, HPA | minAvailable 50% (riq-api, mdm-api); none on rdm-api | preStop sleep 10, grace 30 s | Behind the multi-cluster Gateway, readiness probes OK |
| Async workers | riq-scoring-worker | 4-20, KEDA on Pub/Sub backlog | maxUnavailable 1 | grace 600 s (finishes the current batch) | Pub/Sub ack deadline 600 s; redelivery is safe (idempotent) |
| Long jobs | rdm-nightly-rebuild (CronJob, 02:00-05:30 UTC) | 1 | none | grace 30 s | Not restartable mid-run; a kill means a full restart, 3.5 h |
| Stateful search | mdm-search (3 masters, 6 data pods, local SSD) | StatefulSet | masters minAvailable 2, data maxUnavailable 1 | grace 120 s | Shard relocation after losing a data pod takes 25-40 min; yellow cluster state blocks the next drain |
| Singleton controller | riq-ledger-reconciler | 1 (leader election not implemented) | minAvailable 1 | grace 30 s | A PDB with minAvailable 1 on a single replica allows zero disruptions |
| Platform add-ons | Argo CD (on mgmt), ingress controllers, External Secrets, Prometheus agents (GMP), Crossplane (planned on prod-blue) | varies | mixed | varies | Crossplane providers must not run on two versions of Kubernetes with incompatible CRDs |

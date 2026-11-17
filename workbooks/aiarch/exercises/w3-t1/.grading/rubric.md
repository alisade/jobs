# Rubric: aiarch/w3-t1 Agent never becomes healthy on Runtime
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: amd64 image from a plain docker build on an x86 runner; Runtime needs arm64; exec format error means the process never starts; v2.4.x arm64 because built on Apple silicon. Zero: /ping timing or port. |
| 3 | Evidence | 15 | exec format error lines, imagetools/ECR media type and architecture for both versions, runner tag in the job log. |
| 4 | Fix quality | 10 | arm64 build (ARM runner or buildx + binfmt), immutable tag, blocking gate with its inputs, gate handles index, attestation and single manifests. |
| 5 | Production view | 10 | QEMU vs ARM runner trade-off, digest pinning, scanning, why the gate belongs before deploy. |
Total: 100

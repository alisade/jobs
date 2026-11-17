# Rubric: edgefde/w6-t1 pip and uv fail on the plant build box behind a TLS-inspecting proxy
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Primary root cause | 20 | Full: the inspecting proxy re-signs every proxied connection with a leaf from "Corvane Inspection Issuing CA 2" and sends only the leaf (s_client chain depth 0 only, verify code 20); the bundle the clients use contains only Corvane Root CA G2, so the chain cannot be built: "unable to get local issuer certificate" for the uplink client and for nexus via the proxy. Partial: "missing CA" without identifying the intermediate and the proxy behaviour. |
| 3 | Contributing causes | 15 | NO_PROXY lacks .corvane.internal, so nexus traffic goes through the inspecting proxy (s_client direct to nexus verifies OK with the root alone, via proxy fails). The root-only bundle also lacks public roots, so the pinned, uninspected models.tessellate-edge.example (Let's Encrypt chain to ISRG Root X1) fails for requests and uv (UnknownIssuer). |
| 4 | Evidence | 10 | Quotes the s_client chains and verify codes, the pip and uv errors, the proxy policy lines. |
| 5 | Red herring / workaround | 10 | trusted-host made pip skip verification for those hosts, which is why pip "worked"; it never applied to requests or to the model host for uv, and it is a security finding; allow-insecure-host likewise. |
| 6 | Verification plan | 10 | openssl s_client -CAfile ca-bundle.pem via proxy and direct, curl -v, pip download, uv sync, a requests call, then revert CHG-4471; bundle maintenance on CA rotation. |
Total: 100

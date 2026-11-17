# Reference: aiarch/w3-t1

Root cause: `docker build` on the amd64 GitLab runner produced linux/amd64; AgentCore Runtime
runs arm64 only, so the container fails with exec format error and never answers /ping.
v2.4.x were laptop builds on Apple silicon (arm64). Fix: ARM runner or buildx --platform
linux/arm64 with binfmt; blocking architecture gate (see solution script).

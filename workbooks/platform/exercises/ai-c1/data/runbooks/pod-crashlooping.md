# Pod crash looping

1. Read the last termination reason. OOMKilled means the memory limit is too low for the new version.
2. Compare with the last deploy.

# Reference: aiarch/w6-c1

See `.grading/solution/runbooks/rollback-agent-endpoint.yaml`. The branch after the read gives
the no-op; the backup key includes `{{ automation:EXECUTION_ID }}`; the final aws:branch on the
metric sends high errors to an executeScript step that raises, failing the execution.

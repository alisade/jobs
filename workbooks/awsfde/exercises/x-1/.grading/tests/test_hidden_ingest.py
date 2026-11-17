"""Hidden checks for x-1: idempotency, partial batch failure, poison handling, tenant validation."""

from __future__ import annotations

import pytest
from botocore.stub import ANY
from x1_hidden_support import batch, job_response, jobs, s3_event, sqs_record

from ingest.handler import client_token, handler, parse

KEY = "tenants/acme-foods/docs/returns-policy.pdf"


def _poison(table):
    return [i for i in table.scan()["Items"] if i["pk"] == "POISON"]


def test_start_request_shape_and_token(table, agent):
    obj = parse(__import__("json").dumps(s3_event(KEY)), "tidewater-kb-docs-111122223333")
    tok = client_token(obj)
    assert 33 <= len(tok) <= 256
    agent.stub.add_response("start_ingestion_job", job_response(),
                            {"knowledgeBaseId": "KBACME0001", "dataSourceId": "DSACME0001", "clientToken": tok,
                             "description": ANY})
    assert handler(batch(sqs_record("m-1", s3_event(KEY))), table=table, agent=agent.client)["batchItemFailures"] == []


def test_token_differs_per_object_version_and_is_stable():
    b = "tidewater-kb-docs-111122223333"
    a1 = client_token(parse(__import__("json").dumps(s3_event(KEY, seq="0001")), b))
    a2 = client_token(parse(__import__("json").dumps(s3_event(KEY, seq="0001")), b))
    a3 = client_token(parse(__import__("json").dumps(s3_event(KEY, seq="0002")), b))
    assert a1 == a2 != a3


def test_new_version_of_same_object_is_a_new_job(table, agent):
    agent.stub.add_response("start_ingestion_job", job_response("IJOB000001"))
    agent.stub.add_response("start_ingestion_job", job_response("IJOB000002"))
    handler(batch(sqs_record("m-1", s3_event(KEY, seq="0001"))), table=table, agent=agent.client)
    handler(batch(sqs_record("m-2", s3_event(KEY, seq="0002"))), table=table, agent=agent.client)
    assert len(jobs(table)) == 2


def test_partial_batch_failure_reports_only_the_failed_record(table, agent):
    agent.stub.add_response("start_ingestion_job", job_response())
    agent.stub.add_client_error("start_ingestion_job", "ConflictException", "job already running", 409)
    out = handler(batch(sqs_record("ok-1", s3_event(KEY)),
                        sqs_record("busy-2", s3_event("tenants/corvid-logistics/docs/carrier-sla.pdf")),
                        sqs_record("bad-3", "{not json")), table=table, agent=agent.client)
    assert out == {"batchItemFailures": [{"itemIdentifier": "busy-2"}]}


def test_conflict_then_retry_finishes_the_pending_record(table, agent):
    ev = s3_event("tenants/corvid-logistics/docs/carrier-sla.pdf")
    agent.stub.add_client_error("start_ingestion_job", "ConflictException", "job already running", 409)
    assert handler(batch(sqs_record("m-1", ev)), table=table, agent=agent.client)["batchItemFailures"]
    assert jobs(table)[0]["status"] == "PENDING"
    agent.stub.add_response("start_ingestion_job", job_response(kb="KBCORVID01", ds="DSCORVID01"))
    assert handler(batch(sqs_record("m-1", ev, receive_count=2)), table=table, agent=agent.client)["batchItemFailures"] == []
    js = jobs(table)
    assert len(js) == 1 and js[0]["status"] == "STARTED" and js[0]["ingestion_job_id"] == "IJOB000001"


def test_throttling_is_retried(table, agent):
    agent.stub.add_client_error("start_ingestion_job", "ThrottlingException", "slow down", 429)
    assert handler(batch(sqs_record("m-1", s3_event(KEY))), table=table, agent=agent.client) == \
        {"batchItemFailures": [{"itemIdentifier": "m-1"}]}


@pytest.mark.parametrize("body", [
    "{not json",
    {"source": "aws.s3", "detail-type": "Object Deleted", "detail": {}},
    s3_event(KEY, bucket="someone-elses-bucket"),
    s3_event("uploads/acme-foods/returns-policy.pdf"),
    s3_event("tenants/acme-foods/docs/../../brightline-health/docs/x.pdf"),
    s3_event("tenants/acme-foods/docs/returns-policy.pdf.metadata.json"),
    s3_event("tenants/nobody-inc/docs/x.pdf"),
    s3_event("tenants/old-tenant/docs/x.pdf"),
])
def test_poison_is_recorded_not_redelivered_and_starts_nothing(table, agent, body):
    out = handler(batch(sqs_record("p-1", body)), table=table, agent=agent.client)
    assert out == {"batchItemFailures": []}
    assert jobs(table) == []
    p = _poison(table)
    assert len(p) == 1 and p[0]["sk"] == "MSG#p-1"


def test_duplicate_does_not_call_bedrock_again(table, agent):
    agent.stub.add_response("start_ingestion_job", job_response())
    ev = s3_event(KEY)
    handler(batch(sqs_record("m-1", ev)), table=table, agent=agent.client)
    # no queued response: a second StartIngestionJob call would raise inside the Stubber
    out = handler(batch(sqs_record("m-1-dup", ev), sqs_record("m-1-dup2", ev)), table=table, agent=agent.client)
    assert out == {"batchItemFailures": []}
    agent.stub.assert_no_pending_responses()


def test_job_record_is_tenant_partitioned(table, agent):
    agent.stub.add_response("start_ingestion_job", job_response(kb="KBCORVID01", ds="DSCORVID01"))
    handler(batch(sqs_record("m-1", s3_event("tenants/corvid-logistics/docs/carrier-sla.pdf"))), table=table, agent=agent.client)
    js = jobs(table)
    assert js[0]["pk"] == "TENANT#corvid-logistics" and js[0]["object_key"].endswith("carrier-sla.pdf")

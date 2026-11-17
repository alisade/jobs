"""IAM for the ticket tool: a role whose DynamoDB access is limited to the tenant in its session tag."""

from __future__ import annotations

from typing import Any


def tool_role_policy(table_arn: str) -> dict:
    """Identity policy for the role the tool assumes with a tenant_id session tag.

    ForAllValues + dynamodb:LeadingKeys restricts every partition key in the request to the tenant's
    prefix. No Scan: a Scan has no leading keys, and ForAllValues over an empty set is true, so a
    Scan would be allowed for every tenant.
    """
    tag = "${aws:PrincipalTag/tenant_id}"
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "TenantItemsOnly",
            "Effect": "Allow",
            "Action": ["dynamodb:GetItem", "dynamodb:BatchGetItem", "dynamodb:Query"],
            "Resource": [table_arn, f"{table_arn}/index/*"],
            "Condition": {
                "ForAllValues:StringLike": {"dynamodb:LeadingKeys": [f"TENANT#{tag}", f"TENANT#{tag}#*"]},
                "StringLike": {"aws:PrincipalTag/tenant_id": "?*"},
            },
        }],
    }


def tenant_session(sts: Any, role_arn: str, tenant_id: str, request_id: str) -> dict:
    """Assume the tool role with the tenant as a session tag; returns the Credentials dict."""
    resp = sts.assume_role(RoleArn=role_arn, RoleSessionName=f"ticket-tool-{request_id}"[:64],
                           Tags=[{"Key": "tenant_id", "Value": tenant_id}], DurationSeconds=900)
    return resp["Credentials"]

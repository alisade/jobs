"""IAM for the ticket tool: a role whose DynamoDB access is limited to the tenant in its session tag."""

from __future__ import annotations

from typing import Any


def tool_role_policy(table_arn: str) -> dict:
    """TODO: Allow only the DynamoDB actions the tool needs on the table and its indexes, restricted by dynamodb:LeadingKeys to the TENANT#<tag> prefixes, where the tag is the session tag aws:PrincipalTag/tenant_id. Think about which actions have no leading keys."""
    raise NotImplementedError



def tenant_session(sts: Any, role_arn: str, tenant_id: str, request_id: str) -> dict:
    """TODO: sts.assume_role with a tenant_id session tag; return the Credentials."""
    raise NotImplementedError

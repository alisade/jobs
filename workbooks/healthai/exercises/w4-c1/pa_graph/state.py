"""Graph state for one prior-authorization case. One case = one LangGraph thread."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class PAState(TypedDict, total=False):
    # input
    case_id: str
    member_id: str
    priority: str  # "expedited" | "standard"
    service: str  # generic service label, e.g. "lumbar-mri" (no CPT descriptors)
    diagnosis_codes: list[str]  # ICD-10-CM
    documents: list[str]  # ids of attached clinical documents

    # filled by nodes
    validation_errors: list[str]
    coverage: dict[str, Any]
    missing_info: list[str]
    recommendation: dict[str, Any]  # a validated Recommendation.model_dump(), or {} if invalid
    model_error: str
    review_error: str
    human_decision: dict[str, Any]  # {"decision", "reason", "reviewer"}
    status: str  # "approved" | "denied" | "pended" | "rejected"
    determination: dict[str, Any]

    # append-only audit trail: every node adds one or more entries
    audit: Annotated[list[dict[str, Any]], operator.add]

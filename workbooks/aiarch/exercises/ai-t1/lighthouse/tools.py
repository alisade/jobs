"""Tool specs registered by the help desk agent (works as shipped). Plugins register tools at import
time, so the registry's iteration order depends on which plugins loaded first."""
TOOL_SPECS = {
    "get_ticket": {"description": "Get one IT ticket by id (IT-12345).", "properties": {"ticket_id": {"type": "string"}}},
    "create_ticket": {"description": "Open an IT ticket for the signed-in user.", "properties": {"summary": {"type": "string"}, "category": {"type": "string"}}},
    "list_pending_reviews": {"description": "Pending access reviews for a team.", "properties": {"team": {"type": "string"}}},
    "get_change": {"description": "Get one change ticket (CHG-12345).", "properties": {"change_id": {"type": "string"}}},
    "add_comment": {"description": "Comment on a change ticket.", "properties": {"change_id": {"type": "string"}, "text": {"type": "string"}}},
}


def tool_spec(name: str) -> dict:
    s = TOOL_SPECS[name]
    return {"toolSpec": {"name": name, "description": s["description"],
                         "inputSchema": {"json": {"type": "object", "properties": s["properties"]}}}}

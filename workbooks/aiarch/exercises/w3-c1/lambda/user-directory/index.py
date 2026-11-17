"""User directory tool behind AgentCore Gateway (stub: the real one calls the HR API)."""


def handler(event, context):
    email = (event or {}).get("email", "")
    return {"email": email, "found": email.endswith("@harborpoint.example")}

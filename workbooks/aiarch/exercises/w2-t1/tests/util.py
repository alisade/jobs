from service.testing import ScriptedModel


class Factory:
    """model_factory(name, session_id) -> a fresh ScriptedModel per (name, session)."""

    def __init__(self, turns_per_session=3):
        self.models = {}
        self.turns = turns_per_session

    def __call__(self, name, session_id):
        script = []
        for i in range(self.turns):
            script += [{"tool": "list_pending_reviews", "input": {}}, {"text": f"{session_id} answer {i + 1}"}]
        m = ScriptedModel(script)
        self.models.setdefault((name, session_id), []).append(m)
        return m

    def model(self, session_id):
        return self.models[("access_reviews", session_id)][-1]


def texts(model):
    """All text the model has been shown in its latest call."""
    out = []
    for msg in model.seen[-1]:
        for b in msg["content"]:
            if "text" in b:
                out.append(b["text"])
            if "toolResult" in b:
                out.extend(c.get("text", "") for c in b["toolResult"]["content"])
    return "\n".join(out)

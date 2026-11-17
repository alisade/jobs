from assistant.pipeline import RecordedModel, respond


def replay(question: str) -> dict:
    model = RecordedModel()
    return respond(question, model.outputs[question]["skus"], model)

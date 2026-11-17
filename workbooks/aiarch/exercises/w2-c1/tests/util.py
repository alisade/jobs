from helpdesk.agents import build_orchestrator
from helpdesk.store import Store
from helpdesk.testing import ScriptedModel


def run(scripts, prompt="help", requester="jdiaz", max_model_calls=8):
    models = {k: ScriptedModel(v) for k, v in scripts.items()}
    log, store = [], Store()
    agent = build_orchestrator(lambda n: models[n], store, requester, log, max_model_calls)
    result = agent(prompt)
    return str(result).strip(), models, log, store

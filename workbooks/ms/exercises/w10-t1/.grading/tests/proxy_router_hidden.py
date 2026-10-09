"""Deterministic PROXY for generative orchestration's component selection.

Copilot Studio's real orchestrator is an LLM that reads the name, description and input
descriptions of every topic, tool and knowledge source. This proxy keeps the same inputs
but scores them with TF-IDF cosine similarity, so tests are repeatable offline.

Known limits of the proxy (by design):
- It has no synonyms: use the words your users use (Learn's own advice for descriptions).
- It cannot understand negation, so sentences that contain "not", "never", "don't" etc. are
  IGNORED when scoring. Write "what it does not do" sentences for the real model; they will not
  hurt you here.
- It picks exactly one component per utterance (the real planner can chain several).
"""
from __future__ import annotations

import math
import pathlib
import re
from dataclasses import dataclass

import yaml

STOP = set("""a an and are as at be by can do does for from get got have has having how i i'm in is it
its me my of on or our please the their them they this to up use used uses using want was we what
when where which who will with would you your user users employee employees signed litware
""".split())
NEGATION = re.compile(r"\b(not|never|don't|doesn't|do not|does not|cannot|can't|isn't|won't)\b", re.I)


def stem(w: str) -> str:
    if len(w) > 5 and w.endswith("ing"):
        w = w[:-3]
    if len(w) > 4 and w.endswith("ies"):
        w = w[:-3] + "y"
    elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    return w


def tokens(text: str) -> list[str]:
    return [stem(t) for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOP and len(t) > 1]


def positive_text(text: str) -> str:
    """Drop sentences that contain negation (the proxy cannot interpret them)."""
    parts = re.split(r"(?<=[.;!?])\s+|\n+", text or "")
    return " ".join(p for p in parts if p.strip() and not NEGATION.search(p))


@dataclass
class Component:
    key: str          # e.g. tool:GetPtoBalance
    name: str
    text: str         # what the orchestrator would read


def load_components(agent_dir: pathlib.Path) -> list[Component]:
    comps: list[Component] = []
    for p in sorted((agent_dir / "tools").glob("*.tool.yaml")):
        d = yaml.safe_load(p.read_text()) or {}
        if d.get("disabled"):
            continue
        inputs = " ".join(str(i.get("description") or "") for i in d.get("inputs") or []
                          if i.get("kind") == "AutomaticTaskInput")
        name = str(d.get("modelDisplayName") or "")
        comps.append(Component(f"tool:{p.name[:-10]}", name,
                               f"{name}. {positive_text(str(d.get('modelDescription') or ''))} {positive_text(inputs)}"))
    for p in sorted((agent_dir / "topics").glob("*.topic.yaml")):
        d = yaml.safe_load(p.read_text()) or {}
        if d.get("disabled"):
            continue
        intent = (d.get("beginDialog") or {}).get("intent") or {}
        name = str(intent.get("displayName") or p.name[:-11])
        comps.append(Component(f"topic:{p.name[:-11]}", name,
                               f"{name}. {positive_text(str(d.get('modelDescription') or ''))}"))
    for p in sorted((agent_dir / "knowledge").glob("*.knowledge.yaml")):
        d = yaml.safe_load(p.read_text()) or {}
        if d.get("disabled"):
            continue
        name = str(d.get("displayName") or "")
        comps.append(Component(f"knowledge:{p.name[:-15]}", name,
                               f"{name}. {positive_text(str(d.get('description') or ''))}"))
    return comps


class Router:
    def __init__(self, comps: list[Component]):
        self.comps = comps
        docs = [tokens(c.text) for c in comps]
        n = len(docs)
        df: dict[str, int] = {}
        for d in docs:
            for t in set(d):
                df[t] = df.get(t, 0) + 1
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items()}
        self.vecs = [self._vec(d) for d in docs]

    def _vec(self, toks):
        v: dict[str, float] = {}
        for t in toks:
            if t in self.idf:
                v[t] = v.get(t, 0.0) + self.idf[t]
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {k: x / norm for k, x in v.items()}

    def scores(self, utterance: str) -> list[tuple[str, float]]:
        q = self._vec(tokens(utterance))
        out = [(c.key, sum(q.get(k, 0.0) * w for k, w in vec.items())) for c, vec in zip(self.comps, self.vecs)]
        return sorted(out, key=lambda kv: (-kv[1], kv[0]))

    def route(self, utterance: str) -> str:
        return self.scores(utterance)[0][0]


def router_for(agent_dir) -> Router:
    return Router(load_components(pathlib.Path(agent_dir)))

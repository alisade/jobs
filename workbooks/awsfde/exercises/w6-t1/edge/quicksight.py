"""Fake Quick Sight embedding: issues single-use URLs (valid 5 minutes) bound to the session tags or
user they were generated for, and records what each browser saw when it redeemed a URL."""

from __future__ import annotations

import hashlib


class FakeQuickSight:
    URL_VALID_SECONDS = 300

    def __init__(self) -> None:
        self.urls: dict[str, dict] = {}
        self.clock = 0.0
        self.redeems: list[dict] = []
        self.n = 0

    # boto3-like API used by the Lambda
    def generate_embed_url_for_anonymous_user(self, **kw) -> dict:
        tenant = {t["Key"]: t["Value"] for t in kw.get("SessionTags", [])}.get("tenant_id")
        return self._issue(tenant, "anonymous", kw)

    def generate_embed_url_for_registered_user(self, **kw) -> dict:
        tenant = kw["UserArn"].split(":user/")[1].split("/")[0]
        return self._issue(tenant, kw["UserArn"], kw)

    def _issue(self, tenant: str | None, principal: str, kw: dict) -> dict:
        self.n += 1
        code = hashlib.sha256(f"{self.n}:{tenant}".encode()).hexdigest()[:20]
        url = f"https://us-east-1.quicksight.aws.amazon.com/embed/{code}/dashboards/{kw['ExperienceConfiguration']['Dashboard']['InitialDashboardId']}?code={code}"
        self.urls[url] = {"tenant": tenant, "principal": principal, "issued": self.clock, "used": False,
                          "lifetime_min": kw.get("SessionLifetimeInMinutes", 600)}
        return {"EmbedUrl": url, "Status": 200, "RequestId": f"qs-{self.n:05d}"}

    # what the browser's Embedding SDK does with the URL
    def redeem(self, now: float, url: str, viewer_tenant: str, load_id: str) -> dict:
        u = self.urls.get(url)
        if u is None:
            out = {"result": "invalid"}
        elif u["used"]:
            out = {"result": "already_used"}
        elif now - u["issued"] > self.URL_VALID_SECONDS:
            out = {"result": "expired"}
        else:
            u["used"] = True
            out = {"result": "ok", "data_tenant": u["tenant"]}
        rec = {"t": now, "load_id": load_id, "viewer_tenant": viewer_tenant, "url_code": url.rsplit("=", 1)[-1], **out}
        self.redeems.append(rec)
        return rec

"""List closed pull requests for a repository through the REST API."""

from __future__ import annotations

import logging

log = logging.getLogger("popexport.client")


def fetch_closed_pulls(api, repo: str, per_page: int = 100) -> list[dict]:
    """Return every closed PR in the repository (merged and unmerged)."""
    page = 1
    out: list[dict] = []
    while True:
        resp = api.get(f"/repos/{repo}/pulls", params={"state": "closed", "per_page": per_page, "page": page})
        resp.raise_for_status()
        items = resp.json()
        log.debug("GET %s -> %s (%d items) Link: %s", resp.url, resp.status, len(items), resp.headers.get("Link"))
        out.extend(items)
        if len(items) < per_page:  # a short page is the last page
            break
        page += 1
    log.info("fetched %d closed pulls from %s in %d request(s)", len(out), repo, page)
    return out

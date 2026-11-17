"""List closed pull requests for a repository through the REST API."""

from __future__ import annotations

import logging
import re

log = logging.getLogger("popexport.client")
MAX_PAGES = 1000
_NEXT = re.compile(r'<([^>]+)>\s*;\s*rel="next"')


class PaginationError(RuntimeError):
    pass


def next_link(link_header: str | None) -> str | None:
    if not link_header:
        return None
    m = _NEXT.search(link_header)
    return m.group(1) if m else None


def fetch_closed_pulls(api, repo: str, per_page: int = 100, max_pages: int = MAX_PAGES) -> list[dict]:
    """Return every closed PR in the repository (merged and unmerged).

    Follows the Link rel="next" header until there is none. The server may cap per_page below what
    we ask for, so the size of a page says nothing about whether it is the last one.
    """
    url: str | None = f"/repos/{repo}/pulls"
    params: dict | None = {"state": "closed", "per_page": per_page}
    out: list[dict] = []
    seen: set[str] = set()
    requests = 0
    while url:
        if requests >= max_pages:
            raise PaginationError(f"more than {max_pages} pages from {repo}; refusing to continue")
        resp = api.get(url, params=params)
        requests += 1
        resp.raise_for_status()
        items = resp.json()
        log.debug("GET %s -> %s (%d items) Link: %s", resp.url, resp.status, len(items), resp.headers.get("Link"))
        out.extend(items)
        nxt = next_link(resp.headers.get("Link"))
        if nxt is not None and nxt in seen:
            raise PaginationError(f"pagination loop: {nxt} requested twice")
        if nxt is not None:
            seen.add(nxt)
        url, params = nxt, None
    numbers = [p["number"] for p in out]
    if len(numbers) != len(set(numbers)):
        raise PaginationError("duplicate PRs across pages (the listing changed while paging)")
    log.info("fetched %d closed pulls from %s in %d request(s)", len(out), repo, requests)
    return out

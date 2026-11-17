#!/usr/bin/env python3
"""Build the GitHub Pages site: the whole repo, plus every .md rendered to a sibling .html.

Usage: build_site.py <repo-root> <out-dir> <github-repo-url>
"""
import html
import os
import re
import shutil
import sys
from pathlib import Path

import markdown

SKIP_DIRS = {".git", ".github", "node_modules", ".venv", "__pycache__", ".pytest_cache"}

LINK_FIX = """<script>
/* Site build: .md links open the rendered page; folder links open the folder on GitHub. */
(function () {
  var REPO = "__REPO__";
  var ROOT = new URL("__ROOT__", document.baseURI || location.href);
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a) return;
    var raw = a.getAttribute("href");
    if (!raw || /^(https?:|mailto:|#|javascript:|data:)/i.test(raw)) return;
    var u = new URL(raw, location.href);
    if (u.origin !== location.origin) return;
    if (/\\.md$/i.test(u.pathname)) {
      e.preventDefault();
      u.pathname = u.pathname.replace(/\\.md$/i, ".html");
      location.href = u.href;
    } else if (/\\/$/.test(u.pathname) || !/\\.[A-Za-z0-9]+$/.test(u.pathname)) {
      var rel = u.pathname.indexOf(ROOT.pathname) === 0 ? u.pathname.slice(ROOT.pathname.length) : "";
      if (rel && !/^(index\\.html)?$/.test(rel)) {
        e.preventDefault();
        window.open(REPO + "/tree/main/" + rel.replace(/\\/$/, ""), "_blank", "noopener");
      }
    }
  }, true);
})();
</script>
"""

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root { color-scheme: light dark; --fg:#1f2328; --bg:#ffffff; --muted:#59636e; --line:#d1d9e0; --code:#f6f8fa; --link:#0969da; }
@media (prefers-color-scheme: dark) { :root { --fg:#e6edf3; --bg:#0d1117; --muted:#9198a1; --line:#3d444d; --code:#151b23; --link:#4493f8; } }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
main { max-width: 900px; margin: 0 auto; padding: 24px 20px 64px; }
nav { font-size: 14px; color: var(--muted); border-bottom: 1px solid var(--line); padding-bottom: 10px; margin-bottom: 20px; }
a { color: var(--link); }
h1, h2 { border-bottom: 1px solid var(--line); padding-bottom: .3em; }
code { background: var(--code); padding: .15em .35em; border-radius: 4px; font-size: 90%; }
pre { background: var(--code); padding: 14px; border-radius: 6px; overflow: auto; }
pre code { background: none; padding: 0; }
table { border-collapse: collapse; display: block; overflow: auto; }
th, td { border: 1px solid var(--line); padding: 6px 12px; vertical-align: top; }
blockquote { margin: 0; padding: 0 1em; color: var(--muted); border-left: 4px solid var(--line); }
</style>
</head>
<body>
<main>
<nav><a href="__HOME__">All study plans</a>__EXTRA__ &middot; <a href="__SRC__">View source on GitHub</a></nav>
__BODY__
</main>
__LINKFIX__
</body>
</html>
"""

MD_HREF = re.compile(r'(href=")(?!https?:|mailto:|#)([^"#?]+?)\.md((?:#[^"]*)?")', re.I)


def gh_slug(value, separator="-"):
    # GitHub-style heading anchors: lowercase, drop punctuation, spaces to hyphens (no collapsing).
    value = html.unescape(re.sub(r"<[^>]+>", "", value)).strip().lower()
    value = re.sub(r"[^\w\- ]", "", value)
    return value.replace(" ", separator)


def rel_root(path, out):
    depth = len(path.relative_to(out).parts) - 1
    return "../" * depth or "./"


def link_fix(path, out, repo):
    return LINK_FIX.replace("__REPO__", repo).replace("__ROOT__", rel_root(path, out))


CRUMB_STYLE = 'style="margin:0 0 10px;font-size:14px"'


def plan_for_track(out, track):
    wb = out / "workbooks" / track / "workbook.html"
    if wb.exists():
        m = re.search(r'href="\.\./\.\./([^"/#]+-study-plan\.html|study-plan\.html)', wb.read_text(errors="replace"))
        if m:
            return m.group(1)
    return None


def plan_for_role(out, role):
    for plan in sorted(out.glob("*study-plan.html")):
        if f"study/roles/{role}/" in plan.read_text(errors="replace"):
            return plan.name
    return None


def extra_links(out, dst):
    parts = dst.relative_to(out).parts
    root = rel_root(dst, out)
    links = []
    if len(parts) > 2 and parts[0] == "workbooks" and (out / "workbooks" / parts[1] / "workbook.html").exists():
        plan = plan_for_track(out, parts[1])
        if plan:
            links.append(f'<a href="{root}{plan}">Study plan</a>')
        links.append(f'<a href="{root}workbooks/{parts[1]}/workbook.html">{parts[1]} workbook</a>')
    elif len(parts) > 3 and parts[0] == "study" and parts[1] == "roles":
        plan = plan_for_role(out, parts[2])
        if plan:
            links.append(f'<a href="{root}{plan}">Study plan</a>')
    return "".join(" &middot; " + l for l in links)


def add_crumbs(path, out):
    """Breadcrumbs on plan and workbook pages that do not carry them in source."""
    t = path.read_text(encoding="utf-8", errors="replace")
    if 'class="crumbs"' in t or "<header>" not in t:
        return t
    rel = path.relative_to(out).parts
    links = []
    if len(rel) == 1 and rel[0].endswith("study-plan.html"):
        m = re.search(r'href="(workbooks/[^/"]+/workbook\.html)', t)
        links = ['<a href="README.md">All study plans</a>'] + ([f'<a href="{m.group(1)}">Workbook</a>'] if m else [])
    elif len(rel) == 3 and rel[0] == "workbooks" and rel[2] == "workbook.html":
        plan = plan_for_track(out, rel[1])
        links = ['<a href="../../README.md">All study plans</a>'] + ([f'<a href="../../{plan}">Study plan</a>'] if plan else [])
    if not links:
        return t
    return t.replace("<header>", f'<header>\n  <p class="crumbs" {CRUMB_STYLE}>' + " &middot; ".join(links) + "</p>", 1)


def render_md(src, dst, out, repo, rel):
    text = src.read_text(encoding="utf-8", errors="replace")
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": gh_slug}},
    )
    body = MD_HREF.sub(r"\1\2.html\3", md.convert(text))
    m = re.search(r"^#\s+(.+)$", text, re.M)
    title = m.group(1).strip() if m else src.stem
    root = rel_root(dst, out)
    page = (PAGE.replace("__TITLE__", html.escape(title))
                .replace("__HOME__", root + "index.html")
                .replace("__EXTRA__", extra_links(out, dst))
                .replace("__SRC__", f"{repo}/blob/main/{rel}")
                .replace("__BODY__", body)
                .replace("__LINKFIX__", link_fix(dst, out, repo)))
    dst.write_text(page, encoding="utf-8")


def main():
    root, out, repo = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3].rstrip("/")
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(root, out, ignore=lambda d, names: [n for n in names if n in SKIP_DIRS or Path(d, n).resolve() == out])
    md_count = html_count = 0
    for dirpath, dirnames, filenames in os.walk(out):
        for name in filenames:
            p = Path(dirpath, name)
            rel = p.relative_to(out).as_posix()
            if name.lower().endswith(".md"):
                dst = p.with_suffix(".html")
                if dst.exists():
                    continue
                render_md(p, dst, out, repo, rel)
                md_count += 1
            elif name.lower().endswith(".html"):
                t = add_crumbs(p, out)
                t = MD_HREF.sub(r"\1\2.html\3", t)
                fix = link_fix(p, out, repo)
                t = t.replace("</body>", fix + "</body>", 1) if "</body>" in t else t + fix
                p.write_text(t, encoding="utf-8")
                html_count += 1
    readme = out / "README.html"
    if readme.exists() and not (out / "index.html").exists():
        shutil.copy(readme, out / "index.html")
    for p in out.rglob("*.html"):
        t = p.read_text(encoding="utf-8", errors="replace")
        prefix = "" if rel_root(p, out) == "./" else rel_root(p, out)
        if f'href="{prefix}README.html"' in t:
            p.write_text(t.replace(f'href="{prefix}README.html"', f'href="{prefix}index.html"'), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    print(f"site: {html_count} html pages patched, {md_count} markdown pages rendered -> {out}")


if __name__ == "__main__":
    main()

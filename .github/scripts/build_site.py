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
<nav><a href="__HOME__">Home</a> &middot; <a href="__SRC__">View source on GitHub</a></nav>
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
                t = p.read_text(encoding="utf-8", errors="replace")
                t = MD_HREF.sub(r"\1\2.html\3", t)
                fix = link_fix(p, out, repo)
                t = t.replace("</body>", fix + "</body>", 1) if "</body>" in t else t + fix
                p.write_text(t, encoding="utf-8")
                html_count += 1
    readme = out / "README.html"
    if readme.exists() and not (out / "index.html").exists():
        shutil.copy(readme, out / "index.html")
    (out / ".nojekyll").write_text("")
    print(f"site: {html_count} html pages patched, {md_count} markdown pages rendered -> {out}")


if __name__ == "__main__":
    main()

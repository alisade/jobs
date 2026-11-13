# Sources

| File | Builds |
|---|---|
| `plan.md` + `style.css` | `../AI-Engineer-Agentic-Audit-Learning-Plan.pdf` |
| `build.js` | `../AI-Engineer-Agentic-Audit-Highlights.pptx` |
| `gen.js` | `../AI-Engineer-Agentic-Audit-Highlights.html` and `.pdf` |

Setup: `npm install` in this directory.

```sh
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Learning plan PDF (-smart keeps ASCII quotes)
pandoc -f markdown-smart plan.md -s --embed-resources --css style.css -o plan.html
"${CHROME}" --headless=new --no-pdf-header-footer --print-to-pdf="${PWD}/../AI-Engineer-Agentic-Audit-Learning-Plan.pdf" "file://${PWD}/plan.html"

# PowerPoint deck (needs the pptx skill's apply_theme.js via SKILL_DIR)
SKILL_DIR=<path to pptx skill> NODE_PATH="${PWD}/node_modules" node build.js
mv AI-Engineer-Agentic-Audit-Highlights.pptx ..

# HTML page + PDF
node gen.js
cp highlights.html ../AI-Engineer-Agentic-Audit-Highlights.html
"${CHROME}" --headless=new --no-pdf-header-footer --print-to-pdf="${PWD}/../AI-Engineer-Agentic-Audit-Highlights.pdf" "file://${PWD}/highlights.html"
```

The deck (`build.js`) and the HTML page (`gen.js`) hold separate copies of the slide text; edit both.

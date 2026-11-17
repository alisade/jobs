const fs = require("fs");
const React = require("react");
const R = require("react-dom/server");
const fa = require("react-icons/fa");
const svg = (C) => R.renderToStaticMarkup(React.createElement(C, { size: "100%" }));

const slides = [];
slides.push(`<section class="slide dark">
  <div class="split"><div>
    <h1>AI Engineer: Agentic Audit Controls Testing</h1>
    <p class="sub">Learning plan highlights for a 26-year DevOps engineer</p>
    <p class="date">2026-11-13</p>
  </div><div class="bigicon">${svg(fa.FaRobot)}</div></div>
</section>`);

slides.push(`<section class="slide">
  <h2>The gap is narrower than it looks</h2>
  <div class="stats">
    <div class="stat"><b>4</b><span>strengths that transfer directly</span></div>
    <div class="stat"><b>6</b><span>gaps to close, ranked by priority</span></div>
    <div class="stat gold"><b>6 wks</b><span>to a portfolio project that fits</span></div>
  </div>
  <p class="line"><strong>To learn:</strong> LLM app engineering, agent orchestration, audit vocabulary.
  <strong>Already yours:</strong> infra, security, CI/CD, enterprise integration.</p>
</section>`);

const cards = [
  [fa.FaUserShield, "Approval gates and scoped access", "Change management, Spacelift approvals, PIM, least-privilege IAM. Agents need the same."],
  [fa.FaProjectDiagram, "Orchestration, retries, state", "Step Functions and pipelines are multi-step workflows. Agents add one non-deterministic step."],
  [fa.FaPuzzlePiece, "A skills harness, in daily use", "Your Claude Code setup loads and runs reusable skills. Present it as real experience."],
  [fa.FaClipboardCheck, "The auditee side of ITGC", "SOX at Lakeview, FISMA at GSA. You know what evidence auditors ask for."],
];
slides.push(`<section class="slide">
  <h2>What already transfers</h2>
  <div class="grid2">${cards.map(([I, h, d]) => `<div class="card"><div class="ic">${svg(I)}</div><div><h3>${h}</h3><p>${d}</p></div></div>`).join("")}</div>
</section>`);

const gaps = [
  ["Production Python", "FastAPI, async, Pydantic, google-genai SDK"],
  ["Agent orchestration", "Google ADK, Agent Engine, LangGraph, MCP, A2A"],
  ["Grounding and RAG", "Document Intelligence, AI Search, page-level citations"],
  ["Evaluations", "Golden sets, LLM-as-judge, cost tracking, CI gates"],
  ["LLM security", "Prompt injection, tool scoping, sandboxing, WIF"],
  ["Audit vocabulary", "Design vs effectiveness, IPE, sampling, deficiencies"],
];
slides.push(`<section class="slide">
  <h2>Six gaps, most important first</h2>
  <div class="grid3">${gaps.map(([h, d], i) => `<div class="gap${i === 3 ? " hl" : ""}"><div class="num">${i + 1}</div><h3>${h}</h3><p>${d}</p></div>`).join("")}</div>
</section>`);

slides.push(`<section class="slide">
  <h2>Speak the auditor's language</h2>
  <div class="vocab"><div>
    <ul>
      <li>Test of design vs operating effectiveness</li>
      <li>Population completeness and accuracy (IPE)</li>
      <li>Evidence sufficiency</li>
      <li>Exception, deficiency, significant deficiency, material weakness</li>
      <li>ITGC domains: access, change, operations, SDLC</li>
    </ul>
    <p class="cap">Sources: ISACA ITGC material, PCAOB AS 2201, any Big 4 SOX/ITGC primer</p>
  </div>
  <div class="panel">
    <div class="ph"><span class="sic">${svg(fa.FaBalanceScale)}</span>Sample size by control frequency</div>
    <div class="row"><b>~25</b><span>daily control</span></div>
    <div class="row"><b>2</b><span>quarterly control</span></div>
    <p>Common rule of thumb, not a standard</p>
  </div></div>
</section>`);

const steps = ["Pull population of merged PRs and tickets", "Draw a statistical sample", "Agent checks approval, ticket, SoD, tests",
  "Human review gate for exceptions", "Workpaper with cited evidence", "Evals: accuracy, consistency, cost"];
slides.push(`<section class="slide">
  <h2>Portfolio project: ITGC change tester</h2>
  <div class="steps">${steps.map((t, i) => `<div class="step${i === 3 ? " hl" : ""}"><b>${i + 1}</b><span>${t}</span></div>`).join("")}</div>
  <p class="line"><strong>Stack:</strong> Gemini, ADK, Pydantic, on Azure. Public repo, synthetic or open-source data only.</p>
</section>`);

const phases = [["Weeks 1-2", "Gemini SDK, tool calling, structured outputs, FastAPI"], ["Weeks 3-4", "ADK or LangGraph, state, human-in-the-loop; start project"],
  ["Week 5", "RAG over evidence, citations, Document Intelligence"], ["Week 6", "Evals, tracing, cost, prompt-injection hardening"]];
slides.push(`<section class="slide">
  <h2>A six-week plan</h2>
  <div class="timeline">${phases.map(([h, d], i) => `<div class="ph${i === 3 ? " hl" : ""}"><div class="dot"></div><h3>${h}</h3><p>${d}</p></div>`).join("")}</div>
  <div class="ongoing"><strong>Ongoing:</strong> ITGC/SOX reading, an hour or two a week</div>
</section>`);

slides.push(`<section class="slide dark">
  <div class="split"><div>
    <h1>Make agents safe and operable in production</h1>
    <p class="sub">Most applicants can make a demo work. Few can explain why write tools sit behind an approval gate, and how an auditor would reconstruct what the agent did.</p>
  </div><div class="bigicon">${svg(fa.FaBalanceScale)}</div></div>
</section>`);

const css = `
:root{--ink:#1B2A2F;--deep:#0F3B3A;--teal:#0F6E68;--gold:#C8962E;--pale:#EEF3F1;--muted:#7A8B8A}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-snap-type:y mandatory;background:#2a3436}
body{font-family:Calibri,Carlito,"Segoe UI",-apple-system,Helvetica,Arial,sans-serif;color:var(--ink)}
h1,h2,h3,.stat b,.row b,.step b{font-family:Cambria,Caladea,Georgia,serif}
.deck{display:flex;flex-direction:column;align-items:center;gap:28px;padding:28px 0 90px}
.slide{position:relative;width:min(96vw,calc(88vh*16/9));aspect-ratio:16/9;background:#fff;scroll-snap-align:center;
  box-shadow:0 8px 30px rgba(0,0,0,.35);padding:5% 5% 7%;font-size:min(1.6vw,2.85vh);overflow:hidden;display:flex;flex-direction:column}
.slide:not(.dark)::after{content:"AI Engineer learning plan | 2026-11-13";position:absolute;left:5%;bottom:3.5%;font-size:.7em;color:var(--muted)}
.slide .pg{position:absolute;right:5%;bottom:3.5%;font-size:.7em;color:var(--muted)}
.dark{background:var(--deep);color:#fff;justify-content:center}
.dark .pg{color:#9fb5b2}
h1{font-size:2.6em;line-height:1.1;margin-bottom:.5em}
h2{font-size:2.2em;color:var(--deep);margin-bottom:.8em}
h3{font-size:1.1em;color:var(--deep)}
.sub{font-size:1.15em;color:var(--pale);max-width:30em;line-height:1.4}
.date{margin-top:1em;color:#9fb5b2;font-size:.9em}
.split{display:grid;grid-template-columns:1fr auto;gap:6%;align-items:center}
.bigicon{width:9em;height:9em;border-radius:50%;background:var(--teal);color:var(--gold);padding:2.2em}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:1.4em;margin-bottom:1.4em}
.stat{background:var(--pale);border-radius:.6em;padding:1.2em;text-align:center;display:flex;flex-direction:column;gap:.3em}
.stat b{white-space:nowrap;font-size:3.6em;color:var(--teal);line-height:1}.stat.gold b{color:var(--gold)}
.stat span{font-size:1.05em}
.line{font-size:1.05em;line-height:1.5}.line strong,.ongoing strong{color:var(--teal)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:1.2em}
.card{background:var(--pale);border-radius:.6em;padding:1.1em;display:flex;gap:1em;align-items:flex-start}
.ic{flex:none;width:3.2em;height:3.2em;border-radius:50%;background:var(--teal);color:#fff;padding:.8em}
.card p,.gap p,.ph p{font-size:.92em;line-height:1.35;margin-top:.3em}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:1.1em}
.gap{border:1px solid var(--pale);border-radius:.6em;padding:1em;box-shadow:0 2px 8px rgba(0,0,0,.08);display:grid;grid-template-columns:auto 1fr;column-gap:.7em;align-items:center}
.gap p{grid-column:1/-1;margin-top:.7em}
.num{width:2em;height:2em;border-radius:50%;background:var(--teal);color:#fff;display:grid;place-items:center;font-weight:bold}
.gap.hl .num{background:var(--gold)}
.vocab{display:grid;grid-template-columns:1.5fr 1fr;gap:1.6em;flex:1}
.vocab ul{padding-left:1.1em;font-size:1.05em;line-height:1.35}.vocab li{margin-bottom:.55em}
.cap{font-size:.75em;font-style:italic;color:var(--muted);margin-top:1em}
.panel{background:var(--deep);color:#fff;border-radius:.7em;padding:1.2em}
.panel .ph{font-weight:bold;display:flex;gap:.6em;align-items:center;margin-bottom:.8em}
.sic{width:1.8em;height:1.8em;color:var(--gold);flex:none}
.row{display:flex;align-items:center;gap:.8em;margin:.3em 0}.row b{font-size:2.8em;color:var(--gold);width:2em}
.panel p{font-size:.75em;font-style:italic;color:var(--pale);margin-top:.8em}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:1.6em 2em;margin-bottom:1.3em}
.step{position:relative;background:var(--pale);border-radius:.6em;padding:1em;display:flex;gap:.8em;align-items:center;min-height:4.6em}
.step b{font-size:1.9em;color:var(--teal)}
.step:not(:nth-child(3n))::after{content:"";position:absolute;right:-1.45em;top:50%;transform:translateY(-50%);border:.45em solid transparent;border-left:.65em solid var(--muted)}
.step.hl{background:var(--gold);color:#fff}.step.hl b{color:#fff}
.timeline{display:grid;grid-template-columns:repeat(4,1fr);gap:1.2em;position:relative;margin:.6em 0 1.6em;text-align:center}
.timeline::before{content:"";position:absolute;left:12.5%;right:12.5%;top:.7em;border-top:2px solid var(--muted)}
.dot{width:1.4em;height:1.4em;border-radius:50%;background:var(--teal);border:3px solid #fff;margin:0 auto .8em;position:relative}
.ph.hl .dot{background:var(--gold)}
.ongoing{background:var(--pale);border-radius:.6em;padding:.9em 1.2em;font-size:1.05em}
.nav{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);display:flex;gap:10px;align-items:center;background:rgba(15,59,58,.92);padding:8px 14px;border-radius:999px;color:#fff;font:14px Calibri,Helvetica,sans-serif;z-index:9}
.nav button{background:none;border:1px solid #9fb5b2;color:#fff;border-radius:999px;padding:4px 12px;cursor:pointer;font:inherit}
.nav button:hover{background:var(--teal)}
@media print{
  @page{size:10in 5.625in;margin:0}
  html,body{background:#fff;scroll-snap-type:none}
  .deck{padding:0;gap:0;display:block}
  .slide{width:10in;height:5.625in;aspect-ratio:auto;box-shadow:none;font-size:18px;page-break-after:always;break-after:page;
    -webkit-print-color-adjust:exact;print-color-adjust:exact}
  .nav{display:none}
}`;

const js = `
const S=[...document.querySelectorAll('.slide')];let cur=0;
S.forEach((s,i)=>{const p=document.createElement('div');p.className='pg';p.textContent=(i+1)+' / '+S.length;s.appendChild(p)});
const ind=document.getElementById('ind');
function go(i){cur=Math.max(0,Math.min(S.length-1,i));S[cur].scrollIntoView({behavior:'smooth',block:'center'});ind.textContent=(cur+1)+' / '+S.length}
new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){cur=S.indexOf(e.target);ind.textContent=(cur+1)+' / '+S.length}}),{threshold:.6}).observe&&S.forEach(s=>io.observe(s));
document.addEventListener('keydown',e=>{if(['ArrowDown','ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();go(cur+1)}
 if(['ArrowUp','ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();go(cur-1)}
 if(e.key==='Home')go(0);if(e.key==='End')go(S.length-1);if(e.key==='f')document.documentElement.requestFullscreen&&document.documentElement.requestFullscreen()});
document.getElementById('prev').onclick=()=>go(cur-1);document.getElementById('next').onclick=()=>go(cur+1);`
  .replace("new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){cur=S.indexOf(e.target);ind.textContent=(cur+1)+' / '+S.length}}),{threshold:.6}).observe&&S.forEach(s=>io.observe(s));",
    "const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){cur=S.indexOf(e.target);ind.textContent=(cur+1)+' / '+S.length}}),{threshold:.6});S.forEach(s=>io.observe(s));");

const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Engineer: Agentic Audit Controls Testing - Highlights</title><style>${css}</style></head>
<body><main class="deck">${slides.join("\n")}</main>
<div class="nav"><button id="prev" aria-label="Previous slide">Prev</button><span id="ind">1 / ${slides.length}</span><button id="next" aria-label="Next slide">Next</button><span style="opacity:.7">arrows / space, f = fullscreen</span></div>
<script>${js}</script></body></html>`;
fs.writeFileSync("highlights.html", html);
console.log("ok", slides.length);

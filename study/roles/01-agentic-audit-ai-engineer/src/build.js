const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require(process.env.SKILL_DIR + "/scripts/apply_theme.js");

const THEME = {
  name: "Audit Ledger",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B2A2F", lt1: "FFFFFF", dk2: "0F3B3A", lt2: "EEF3F1",
    accent1: "0F6E68", accent2: "C8962E", accent3: "5B7F95",
    accent4: "A23B3B", accent5: "7A8B8A", accent6: "2E8B57",
    hlink: "0F6E68", folHlink: "5B7F95",
  },
};

async function icon(Comp, hex) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + hex, size: 256 }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; // 10 x 5.625
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = "AI Engineer - Agentic Audit Controls Testing - Learning Plan Highlights";
  const C = pres.SchemeColor;

  pres.defineSlideMaster({
    title: "Title Dark",
    background: { color: C.text2 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.5, w: 6.2, h: 1.6, fontSize: 38, bold: true, color: C.background1, valign: "bottom", align: "left", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "subtitle", type: "body", x: 0.6, y: 3.3, w: 6.2, h: 0.9, fontSize: 16, color: C.background2, valign: "top", align: "left", margin: 0 }, text: "" } },
    ],
  });
  pres.defineSlideMaster({
    title: "Title Only",
    background: { color: C.background1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.75, fontSize: 32, bold: true, color: C.text2, valign: "middle", align: "left", margin: 0 }, text: "" } },
      { text: { text: "AI Engineer learning plan | 2026-11-13", options: { x: 0.5, y: 5.2, w: 6, h: 0.3, fontSize: 10, color: C.accent5, margin: 0 } } },
    ],
    slideNumber: { x: 9.0, y: 5.2, w: 0.5, h: 0.3, fontSize: 10, color: C.accent5, align: "right" },
  });

  const white = THEME.colors.lt1, gold = THEME.colors.accent2;
  const ic = {
    robot: await icon(fa.FaRobot, gold),
    shield: await icon(fa.FaUserShield, white),
    flow: await icon(fa.FaProjectDiagram, white),
    puzzle: await icon(fa.FaPuzzlePiece, white),
    check: await icon(fa.FaClipboardCheck, white),
    gavel: await icon(fa.FaBalanceScale, gold),
  };
  const shadow = () => ({ type: "outer", color: "000000", opacity: 0.12, blur: 6, offset: 2, angle: 90 });

  // 1. Title
  pres.addSection({ title: "Overview" });
  let s = pres.addSlide({ masterName: "Title Dark", sectionTitle: "Overview" });
  s.addText("AI Engineer: Agentic Audit Controls Testing", { placeholder: "title" });
  s.addText("Learning plan highlights for a 26-year DevOps engineer", { placeholder: "subtitle" });
  s.addShape(pres.shapes.OVAL, { x: 7.2, y: 1.55, w: 2.2, h: 2.2, fill: { color: C.accent1 }, objectName: "Icon circle" });
  s.addImage({ data: ic.robot, x: 7.7, y: 2.05, w: 1.2, h: 1.2, altText: "Robot icon", objectName: "Robot icon" });
  s.addNotes("A highlights version of the full learning plan PDF. Target role: hands-on AI engineer building an agentic audit controls testing app on Azure with Gemini.");

  // 2. Bottom line
  s = pres.addSlide({ masterName: "Title Only", sectionTitle: "Overview" });
  s.addText("The gap is narrower than it looks", { placeholder: "title" });
  const stats = [["4", "strengths that\ntransfer directly"], ["6", "gaps to close,\nranked by priority"], ["6 wks", "to a portfolio\nproject that fits"]];
  stats.forEach(([n, l], i) => {
    const x = 0.5 + i * 3.1;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.35, w: 2.8, h: 2.3, rectRadius: 0.12, fill: { color: C.background2 }, objectName: "Stat card " + (i + 1) });
    s.addText(n, { x, y: 1.5, w: 2.8, h: 1.1, fontSize: 54, bold: true, fontFace: THEME.headFontFace, color: i === 2 ? C.accent2 : C.accent1, align: "center", isTextBox: true, objectName: "Stat value " + (i + 1) });
    s.addText(l, { x, y: 2.6, w: 2.8, h: 0.85, fontSize: 15, color: C.text1, align: "center", isTextBox: true, objectName: "Stat label " + (i + 1) });
  });
  s.addText([
    { text: "To learn: ", options: { bold: true, color: C.accent1 } },
    { text: "LLM app engineering, agent orchestration, audit vocabulary.  " },
    { text: "Already yours: ", options: { bold: true, color: C.accent1 } },
    { text: "infra, security, CI/CD, enterprise integration." },
  ], { x: 0.5, y: 3.95, w: 9.0, h: 0.8, fontSize: 15, color: C.text1, isTextBox: true, objectName: "Summary line" });
  s.addNotes("Main message: this is not a career change, it is an extension. Most of the hard production skills are already there.");

  // 3. Transfers
  pres.addSection({ title: "Where you stand" });
  s = pres.addSlide({ masterName: "Title Only", sectionTitle: "Where you stand" });
  s.addText("What already transfers", { placeholder: "title" });
  const cards = [
    [ic.shield, "Approval gates and scoped access", "Change management, Spacelift approvals, PIM, least-privilege IAM. Agents need the same."],
    [ic.flow, "Orchestration, retries, state", "Step Functions and pipelines are multi-step workflows. Agents add one non-deterministic step."],
    [ic.puzzle, "A skills harness, in daily use", "Your Claude Code setup loads and runs reusable skills. Present it as real experience."],
    [ic.check, "The auditee side of ITGC", "SOX at Lakeview, FISMA at GSA. You know what evidence auditors ask for."],
  ];
  cards.forEach(([img, h, d], i) => {
    const x = 0.5 + (i % 2) * 4.6, y = 1.3 + Math.floor(i / 2) * 1.9;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 4.4, h: 1.65, rectRadius: 0.1, fill: { color: C.background2 }, objectName: "Card " + (i + 1) });
    s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: y + 0.3, w: 0.75, h: 0.75, fill: { color: C.accent1 }, objectName: "Card icon circle " + (i + 1) });
    s.addImage({ data: img, x: x + 0.43, y: y + 0.48, w: 0.39, h: 0.39, altText: h, objectName: "Card icon " + (i + 1) });
    s.addText(h, { x: x + 1.2, y: y + 0.18, w: 3.05, h: 0.45, fontSize: 16, bold: true, color: C.text2, margin: 0, valign: "middle", isTextBox: true, objectName: "Card title " + (i + 1) });
    s.addText(d, { x: x + 1.2, y: y + 0.65, w: 3.05, h: 0.85, fontSize: 13, color: C.text1, margin: 0, valign: "top", isTextBox: true, objectName: "Card text " + (i + 1) });
  });
  s.addNotes("Lead interviews with these four. The skills-harness point maps directly to the posting's preferred experience: building AI harnesses that load and execute reusable skills.");

  // 4. Six gaps
  pres.addSection({ title: "What to learn" });
  s = pres.addSlide({ masterName: "Title Only", sectionTitle: "What to learn" });
  s.addText("Six gaps, most important first", { placeholder: "title" });
  const gaps = [
    ["Production Python", "FastAPI, async, Pydantic, google-genai SDK"],
    ["Agent orchestration", "Google ADK, Agent Engine, LangGraph, MCP, A2A"],
    ["Grounding and RAG", "Document Intelligence, AI Search, page-level citations"],
    ["Evaluations", "Golden sets, LLM-as-judge, cost tracking, CI gates"],
    ["LLM security", "Prompt injection, tool scoping, sandboxing, WIF"],
    ["Audit vocabulary", "Design vs effectiveness, IPE, sampling, deficiencies"],
  ];
  gaps.forEach(([h, d], i) => {
    const x = 0.5 + (i % 3) * 3.05, y = 1.3 + Math.floor(i / 3) * 1.9;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.85, h: 1.7, rectRadius: 0.1, fill: { color: C.background1 }, line: { color: C.background2, width: 1 }, shadow: shadow(), objectName: "Gap card " + (i + 1) });
    s.addShape(pres.shapes.OVAL, { x: x + 0.2, y: y + 0.2, w: 0.5, h: 0.5, fill: { color: i === 3 ? C.accent2 : C.accent1 }, objectName: "Gap number circle " + (i + 1) });
    s.addText(String(i + 1), { x: x + 0.2, y: y + 0.2, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "Gap number " + (i + 1) });
    s.addText(h, { x: x + 0.85, y: y + 0.2, w: 1.9, h: 0.5, fontSize: 15, bold: true, color: C.text2, valign: "middle", margin: 0, isTextBox: true, objectName: "Gap title " + (i + 1) });
    s.addText(d, { x: x + 0.2, y: y + 0.85, w: 2.5, h: 0.75, fontSize: 13, color: C.text1, valign: "top", margin: 0, isTextBox: true, objectName: "Gap text " + (i + 1) });
  });
  s.addNotes("Evaluations is highlighted in gold: it is what separates hobbyists from people who get hired. Google has renamed its agent products several times; check current docs for exact names.");

  // 5. Audit vocabulary
  s = pres.addSlide({ masterName: "Title Only", sectionTitle: "What to learn" });
  s.addText("Speak the auditor's language", { placeholder: "title" });
  s.addText([
    { text: "Test of design vs operating effectiveness", options: { bullet: true, breakLine: true } },
    { text: "Population completeness and accuracy (IPE)", options: { bullet: true, breakLine: true } },
    { text: "Evidence sufficiency", options: { bullet: true, breakLine: true } },
    { text: "Exception, deficiency, significant deficiency, material weakness", options: { bullet: true, breakLine: true } },
    { text: "ITGC domains: access, change, operations, SDLC", options: { bullet: true } },
  ], { x: 0.5, y: 1.3, w: 5.2, h: 2.9, fontSize: 15, color: C.text1, paraSpaceAfter: 8, valign: "top", isTextBox: true, objectName: "Audit terms" });
  s.addText("Sources: ISACA ITGC material, PCAOB AS 2201, any Big 4 SOX/ITGC primer", { x: 0.5, y: 4.35, w: 5.2, h: 0.5, fontSize: 11, italic: true, color: C.accent5, isTextBox: true, objectName: "Sources" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.1, y: 1.3, w: 3.4, h: 3.55, rectRadius: 0.12, fill: { color: C.text2 }, objectName: "Sampling panel" });
  s.addImage({ data: ic.gavel, x: 6.4, y: 1.5, w: 0.45, h: 0.45, altText: "Scales icon", objectName: "Scales icon" });
  s.addText("Sample size by control frequency", { x: 6.95, y: 1.45, w: 2.4, h: 0.55, fontSize: 13, bold: true, color: C.background1, valign: "middle", margin: 0, isTextBox: true, objectName: "Panel heading" });
  s.addText("~25", { x: 6.4, y: 2.1, w: 1.5, h: 0.9, fontSize: 44, bold: true, fontFace: THEME.headFontFace, color: C.accent2, margin: 0, isTextBox: true, objectName: "Daily stat" });
  s.addText("daily control", { x: 7.9, y: 2.1, w: 1.5, h: 0.9, fontSize: 14, color: C.background1, valign: "middle", margin: 0, isTextBox: true, objectName: "Daily label" });
  s.addText("2", { x: 6.4, y: 3.05, w: 1.5, h: 0.9, fontSize: 44, bold: true, fontFace: THEME.headFontFace, color: C.accent2, margin: 0, isTextBox: true, objectName: "Quarterly stat" });
  s.addText("quarterly control", { x: 7.9, y: 3.05, w: 1.5, h: 0.9, fontSize: 14, color: C.background1, valign: "middle", margin: 0, isTextBox: true, objectName: "Quarterly label" });
  s.addText("Common rule of thumb, not a standard", { x: 6.4, y: 4.1, w: 2.9, h: 0.5, fontSize: 11, italic: true, color: C.background2, margin: 0, isTextBox: true, objectName: "Panel caption" });
  s.addNotes("Budget an hour or two a week for this, ongoing. Sample sizes vary by firm methodology and risk; 25 daily / 2 quarterly is a common rule of thumb.");

  // 6. Portfolio project
  pres.addSection({ title: "How to prove it" });
  s = pres.addSlide({ masterName: "Title Only", sectionTitle: "How to prove it" });
  s.addText("Portfolio project: ITGC change tester", { placeholder: "title" });
  const steps = ["Pull population of merged PRs and tickets", "Draw a statistical sample", "Agent checks approval, ticket, SoD, tests",
                 "Human review gate for exceptions", "Workpaper with cited evidence", "Evals: accuracy, consistency, cost"];
  steps.forEach((t, i) => {
    const x = 0.5 + (i % 3) * 3.1, y = 1.25 + Math.floor(i / 3) * 1.45;
    const hl = i === 3;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.7, h: 1.15, rectRadius: 0.1, fill: { color: hl ? C.accent2 : C.background2 }, objectName: "Step box " + (i + 1) });
    s.addText(String(i + 1), { x: x + 0.15, y, w: 0.45, h: 1.15, fontSize: 26, bold: true, fontFace: THEME.headFontFace, color: hl ? C.background1 : C.accent1, valign: "middle", margin: 0, isTextBox: true, objectName: "Step number " + (i + 1) });
    s.addText(t, { x: x + 0.65, y, w: 1.95, h: 1.15, fontSize: 14, color: hl ? C.background1 : C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: "Step text " + (i + 1) });
    if (i % 3 !== 2) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + 2.78, y: y + 0.45, w: 0.24, h: 0.25, fill: { color: C.accent5 }, objectName: "Step arrow " + (i + 1) });
  });
  s.addText([
    { text: "Stack: ", options: { bold: true, color: C.accent1 } },
    { text: "Gemini, ADK, Pydantic, on Azure. Public repo, synthetic or open-source data only." },
  ], { x: 0.5, y: 4.3, w: 9.0, h: 0.5, fontSize: 14, color: C.text1, isTextBox: true, objectName: "Stack line" });
  s.addNotes("This one project demonstrates nearly every requirement in the posting. Do not use GSA or Lakeview data. SoD = segregation of duties: approver differs from author.");

  // 7. Timeline
  s = pres.addSlide({ masterName: "Title Only", sectionTitle: "How to prove it" });
  s.addText("A six-week plan", { placeholder: "title" });
  const phases = [
    ["Weeks 1-2", "Gemini SDK, tool calling, structured outputs, FastAPI"],
    ["Weeks 3-4", "ADK or LangGraph, state, human-in-the-loop; start project"],
    ["Week 5", "RAG over evidence, citations, Document Intelligence"],
    ["Week 6", "Evals, tracing, cost, prompt-injection hardening"],
  ];
  s.addShape(pres.shapes.LINE, { x: 0.9, y: 1.85, w: 8.2, h: 0, line: { color: C.accent5, width: 2 }, objectName: "Timeline line" });
  phases.forEach(([h, d], i) => {
    const cx = 0.9 + i * (8.2 / 3);
    s.addShape(pres.shapes.OVAL, { x: cx - 0.2, y: 1.65, w: 0.4, h: 0.4, fill: { color: i === 3 ? C.accent2 : C.accent1 }, line: { color: C.background1, width: 3 }, objectName: "Milestone " + (i + 1) });
    const bx = Math.min(Math.max(cx - 1.05, 0.5), 9.5 - 2.1);
    s.addText(h, { x: bx, y: 2.25, w: 2.1, h: 0.45, fontSize: 17, bold: true, color: C.text2, align: "center", margin: 0, isTextBox: true, objectName: "Phase title " + (i + 1) });
    s.addText(d, { x: bx, y: 2.7, w: 2.1, h: 1.1, fontSize: 13, color: C.text1, align: "center", valign: "top", margin: 0, isTextBox: true, objectName: "Phase text " + (i + 1) });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 4.05, w: 9.0, h: 0.7, rectRadius: 0.1, fill: { color: C.background2 }, objectName: "Ongoing box" });
  s.addText([
    { text: "Ongoing: ", options: { bold: true, color: C.accent1 } },
    { text: "ITGC/SOX reading, an hour or two a week" },
  ], { x: 0.75, y: 4.05, w: 8.5, h: 0.7, fontSize: 14, color: C.text1, valign: "middle", margin: 0, isTextBox: true, objectName: "Ongoing text" });
  s.addNotes("Week 6 is highlighted: evals and hardening are what make the project credible to this employer.");

  // 8. Closing
  pres.addSection({ title: "Positioning" });
  s = pres.addSlide({ masterName: "Title Dark", sectionTitle: "Positioning" });
  s.addText("Make agents safe and operable in production", { placeholder: "title" });
  s.addText("Most applicants can make a demo work. Few can explain why write tools sit behind an approval gate, and how an auditor would reconstruct what the agent did.", { placeholder: "subtitle" });
  s.addShape(pres.shapes.OVAL, { x: 7.2, y: 1.55, w: 2.2, h: 2.2, fill: { color: C.accent1 }, objectName: "Icon circle" });
  s.addImage({ data: ic.gavel, x: 7.7, y: 2.05, w: 1.2, h: 1.2, altText: "Scales icon", objectName: "Scales icon large" });
  s.addNotes("The interview pitch in one line. Back it with the portfolio project and the four transferable strengths.");

  const out = "AI-Engineer-Agentic-Audit-Highlights.pptx";
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();

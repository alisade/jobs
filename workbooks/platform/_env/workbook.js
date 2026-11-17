(function () {
  var KEY = "wb-platform-v1";
  var PASS = 70;
  var D = window.PLATFORM_DATA || { areas: [], weekly: [], mocks: {} };
  var state = {};
  try { state = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { state = {}; }
  state.q = state.q || {};
  state.mock = state.mock || {};
  state.mockRun = state.mockRun || {};
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* storage blocked: keep in memory */ } }
  var G = window.GRADES || {};

  // ---------- theme ----------
  function applyTheme() {
    if (state.theme) document.documentElement.setAttribute("data-theme", state.theme);
    else document.documentElement.removeAttribute("data-theme");
  }
  applyTheme();
  document.getElementById("themebtn").addEventListener("click", function () {
    var dark = state.theme ? state.theme === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    state.theme = dark ? "light" : "dark"; save(); applyTheme();
  });

  // ---------- tabs ----------
  var pages = Array.prototype.slice.call(document.querySelectorAll("section.page"));
  var tabs = document.getElementById("tabs");
  pages.forEach(function (p) {
    var a = document.createElement("a");
    a.href = "#" + p.id; a.dataset.page = p.id;
    a.innerHTML = p.dataset.title + '<span class="pct"></span>';
    tabs.appendChild(a);
  });
  function show() {
    var id = (location.hash || "#overview").slice(1);
    var target = document.getElementById(id);
    var page = target ? (target.classList.contains("page") ? target : target.closest("section.page")) : null;
    if (!page) page = document.getElementById("overview");
    pages.forEach(function (p) { p.classList.toggle("active", p === page); });
    tabs.querySelectorAll("a").forEach(function (a) { a.classList.toggle("active", a.dataset.page === page.id); });
    if (target && target !== page) target.scrollIntoView(); else window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", show);

  // ---------- grades ----------
  function fbHref(fb) {
    if (!fb) return null;
    if (fb.indexOf("grades/") === 0) return "../" + fb;
    return "../grades/" + fb;
  }
  function gradeInfo(id) {
    var g = G[id];
    if (!g || !g.attempts || !g.attempts.length) return null;
    var last = g.attempts[g.attempts.length - 1];
    return { latest: g.latest, best: g.best, attempts: g.attempts.length, passed: g.best >= PASS,
             feedback: fbHref(last.feedback), ts: last.ts, summary: last.summary };
  }
  document.querySelectorAll("[data-badge]").forEach(function (b) {
    var gi = gradeInfo(b.dataset.badge);
    if (!gi) { b.textContent = "not attempted"; return; }
    b.classList.add(gi.passed ? "pass" : "retry");
    b.innerHTML = "latest " + gi.latest + " / best " + gi.best + " - " + (gi.passed ? "PASS" : "RETRY") +
      (gi.feedback ? ' - <a href="' + gi.feedback + '">feedback</a>' : "");
    b.title = gi.summary || "";
  });
  function weekPct(pageId) {
    var cards = document.querySelectorAll('#' + pageId + ' [data-ex]');
    if (!cards.length) return null;
    var done = 0;
    cards.forEach(function (c) { var gi = gradeInfo(c.dataset.ex); if (gi && gi.passed) done++; });
    return Math.round(100 * done / cards.length);
  }

  // ---------- questions ----------
  var AREAS = D.areas;
  function areaOf(key) { return AREAS.filter(function (a) { return a.key === key; })[0] || { key: key, name: key }; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function sameSet(a, b) { if (a.length !== b.length) return false; return a.slice().sort().join(",") === b.slice().sort().join(","); }
  function isCorrect(q, resp) {
    if (!resp) return false;
    if (q.type === "order") return resp.length === q.answer.length && resp.join(",") === q.answer.join(",");
    return sameSet(resp.map(Number), q.answer.map(Number));
  }
  function askText(q) {
    if (q.type === "multi") return "Choose " + (q.choose || q.answer.length) + ". Scored all or nothing.";
    if (q.type === "order") return "Arrange " + (q.choose || q.answer.length) + " of the actions in the correct order. Not every action is used.";
    return "Choose one.";
  }
  function renderQ(q, num, mode, getResp, setResp, reveal) {
    var el = document.createElement("div");
    el.className = "q"; el.dataset.qid = q.id;
    var area = areaOf(q.area);
    var typeLabel = q.type === "multi" ? "multi-select" : (q.type === "order" ? "build list" : "single answer");
    el.innerHTML = '<div class="qhead"><b>Q' + num + '</b><span class="area">' + esc(area.name) + '</span><span>' + typeLabel +
      '</span><span>' + esc(q.id) + '</span></div><div class="stem">' + q.stem + '</div><p class="small">' + askText(q) + '</p>';
    var body = document.createElement("div");
    var resp = getResp();
    var inputs = [];
    if (q.type === "order") {
      var ol = document.createElement("ol"); ol.className = "actions"; ol.type = "A";
      q.options.forEach(function (o) { var li = document.createElement("li"); li.innerHTML = o; ol.appendChild(li); });
      body.appendChild(ol);
      var seq = document.createElement("div"); seq.className = "seq";
      var n = q.choose || q.answer.length;
      for (var i = 0; i < n; i++) {
        var lab = document.createElement("span"); lab.textContent = "Step " + (i + 1);
        var sel = document.createElement("select");
        var o0 = document.createElement("option"); o0.value = ""; o0.textContent = "- choose an action -"; sel.appendChild(o0);
        q.options.forEach(function (o, j) {
          var op = document.createElement("option"); op.value = String(j);
          var tmp = document.createElement("div"); tmp.innerHTML = o;
          op.textContent = String.fromCharCode(65 + j) + ". " + tmp.textContent; sel.appendChild(op);
        });
        if (resp && resp[i] !== undefined && resp[i] !== null) sel.value = String(resp[i]);
        seq.appendChild(lab); seq.appendChild(sel); inputs.push(sel);
      }
      body.appendChild(seq);
    } else {
      q.options.forEach(function (o, j) {
        var lab = document.createElement("label"); lab.className = "opt";
        var inp = document.createElement("input");
        inp.type = q.type === "multi" ? "checkbox" : "radio";
        inp.name = mode + "-" + q.id; inp.value = String(j);
        if (resp && resp.map(Number).indexOf(j) >= 0) inp.checked = true;
        var span = document.createElement("span"); span.innerHTML = String.fromCharCode(65 + j) + ". " + o;
        lab.appendChild(inp); lab.appendChild(span); body.appendChild(lab); inputs.push(inp);
      });
    }
    el.appendChild(body);
    function readResp() {
      if (q.type === "order") return inputs.map(function (s) { return s.value === "" ? null : Number(s.value); });
      return inputs.filter(function (i) { return i.checked; }).map(function (i) { return Number(i.value); });
    }
    inputs.forEach(function (inp) { inp.addEventListener("change", function () { setResp(readResp(), false); }); });
    var explain = document.createElement("div");
    function showExplain() {
      var r = getResp(); var ok = isCorrect(q, r);
      explain.className = "explain" + (ok ? "" : " bad");
      var key;
      if (q.type === "order") key = q.answer.map(function (j, k) { return (k + 1) + ". " + String.fromCharCode(65 + j); }).join("  ");
      else key = q.answer.map(function (j) { return String.fromCharCode(65 + j); }).join(", ");
      var links = (q.learn || []).map(function (l) { return '<a href="' + esc(l.href) + '">' + esc(l.label) + "</a>"; }).join(" / ");
      explain.innerHTML = '<b class="' + (ok ? "ok" : "no") + '">' + (ok ? "Correct." : "Incorrect.") + "</b> Answer: " + key +
        "<br>" + q.explanation + (links ? '<br><span class="small">Learn: ' + links + "</span>" : "");
      if (q.type !== "order") {
        body.querySelectorAll("label.opt").forEach(function (lab, j) {
          lab.classList.toggle("right", q.answer.map(Number).indexOf(j) >= 0);
          lab.classList.toggle("wrong", (r || []).indexOf(j) >= 0 && q.answer.map(Number).indexOf(j) < 0);
        });
      }
      if (!explain.parentNode) el.appendChild(explain);
    }
    if (mode === "practice") {
      var row = document.createElement("div"); row.className = "actionsrow";
      var b = document.createElement("button"); b.className = "btn"; b.textContent = "Check answer";
      b.addEventListener("click", function () { setResp(readResp(), true); showExplain(); });
      var clr = document.createElement("button"); clr.className = "btn"; clr.textContent = "Reset";
      clr.addEventListener("click", function () { setResp(null, false); var nq = renderQ(q, num, mode, getResp, setResp, false); el.parentNode.replaceChild(nq, el); });
      row.appendChild(b); row.appendChild(clr); el.appendChild(row);
    } else {
      inputs.forEach(function (i) { i.disabled = !!reveal; });
    }
    if (reveal) showExplain();
    return el;
  }
  function renderList(container, list, mode, getResp, setResp, revealFn) {
    list.forEach(function (q, i) {
      container.appendChild(renderQ(q, i + 1, mode,
        function () { return getResp(q); }, function (r, checked) { setResp(q, r, checked); }, revealFn(q)));
    });
  }

  // ---------- weekly practice ----------
  var SETS = [];
  (function () {
    var by = {};
    D.weekly.forEach(function (q) { var w = String(q.week); (by[w] = by[w] || []).push(q); });
    Object.keys(by).sort(function (a, b) { return (a === "ai") - (b === "ai") || Number(a) - Number(b); }).forEach(function (w) {
      SETS.push({ key: "w" + w, label: w === "ai" ? "AI Integration" : "Week " + w, list: by[w] });
    });
  })();
  function setScore(list) {
    var answered = 0, right = 0;
    list.forEach(function (q) { var s = state.q[q.id]; if (s && s.checked) { answered++; if (isCorrect(q, s.r)) right++; } });
    return { answered: answered, right: right, total: list.length };
  }
  var MOCKS = [["screen", D.mocks.screen], ["gcp", D.mocks.gcp]].filter(function (m) { return m[1]; });

  var seRoot = document.getElementById("se-root");
  var seNav = document.getElementById("se-nav");
  var current = state.seView || "w1";
  function buildNav() {
    seNav.innerHTML = "";
    SETS.forEach(function (s) {
      var b = document.createElement("button"); b.textContent = s.label; b.dataset.view = s.key; seNav.appendChild(b);
    });
    MOCKS.forEach(function (m) {
      var b = document.createElement("button"); b.textContent = "Mock: " + m[1].short; b.dataset.view = "mock:" + m[0]; seNav.appendChild(b);
    });
    seNav.querySelectorAll("button").forEach(function (b) {
      b.classList.toggle("active", b.dataset.view === current);
      b.addEventListener("click", function () { current = b.dataset.view; state.seView = current; save(); buildNav(); renderView(); });
    });
  }
  function renderView() {
    seRoot.innerHTML = "";
    if (timerHandle) { clearInterval(timerHandle); timerHandle = null; }
    if (current.indexOf("mock:") === 0) {
      var key = current.slice(5);
      var m = MOCKS.filter(function (x) { return x[0] === key; })[0];
      if (m) { renderMock(key, m[1]); return; }
      current = "w1";
    }
    var set = SETS.filter(function (s) { return s.key === current; })[0] || SETS[0];
    if (!set) { seRoot.textContent = "No questions loaded."; return; }
    var list = set.list;
    var head = document.createElement("div"); head.className = "card";
    head.innerHTML = "<b>" + esc(set.label) + "</b>: " + list.length +
      ' questions. <span id="se-score"></span> Answers save in this browser. <button class="btn" id="se-reset">Reset this set</button>';
    function headScore() { var s2 = setScore(list); head.querySelector("#se-score").textContent = "Score so far: " + s2.right + " / " + s2.answered + " checked (" + s2.total + " total)."; }
    seRoot.appendChild(head);
    head.querySelector("#se-reset").addEventListener("click", function () {
      if (!confirm("Clear your answers for this set?")) return;
      list.forEach(function (q) { delete state.q[q.id]; }); save(); renderView(); refreshScore();
    });
    headScore();
    renderList(seRoot, list, "practice",
      function (q) { return state.q[q.id] ? state.q[q.id].r : null; },
      function (q, r, checked) {
        if (r === null) delete state.q[q.id];
        else state.q[q.id] = { r: r, checked: !!checked };
        save(); refreshScore(); headScore();
      },
      function (q) { return !!(state.q[q.id] && state.q[q.id].checked); });
  }

  // ---------- mock exams ----------
  var timerHandle = null;
  function fmt(sec) { sec = Math.max(0, Math.floor(sec)); var m = Math.floor(sec / 60), s = sec % 60; return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s; }
  function scaled(mock, right, total) {
    if (mock.scale === "aws") return Math.round(100 + 900 * right / total);
    return Math.round(100 * right / total);
  }
  function passed(mock, score) { return score >= mock.pass; }
  function scoreMock(mock, run) {
    var byArea = {}; var right = 0; var wrong = [];
    mock.questions.forEach(function (q) {
      var a = byArea[q.area] = byArea[q.area] || { right: 0, total: 0 };
      a.total++;
      if (isCorrect(q, run.answers[q.id])) { a.right++; right++; } else wrong.push(q.id);
    });
    return { score: scaled(mock, right, mock.questions.length), right: right, total: mock.questions.length, byArea: byArea, wrong: wrong };
  }
  function answeredCount(run) {
    return Object.keys(run.answers).filter(function (k) { var r = run.answers[k]; return r && r.length && r.some(function (x) { return x !== null; }); }).length;
  }
  function finishMock(key, mock, auto) {
    var run = state.mockRun[key]; if (!run) return;
    var res = scoreMock(mock, run);
    res.ts = new Date().toISOString().slice(0, 19);
    res.minutes = Math.round((Math.min(Date.now(), run.deadline) - run.started) / 60000);
    res.auto = !!auto; res.answers = run.answers;
    (state.mock[key] = state.mock[key] || []).push(res);
    delete state.mockRun[key]; save();
    if (timerHandle) { clearInterval(timerHandle); timerHandle = null; }
    refreshScore(); renderView();
  }
  function renderMock(key, mock) {
    var run = state.mockRun[key];
    var hist = state.mock[key] || [];
    var counts = {}; mock.questions.forEach(function (q) { counts[q.area] = (counts[q.area] || 0) + 1; });
    if (!run) {
      var intro = document.createElement("div"); intro.className = "card";
      var mix = AREAS.filter(function (a) { return counts[a.key]; }).map(function (a) { return "<li>" + esc(a.name) + ": " + counts[a.key] + " questions</li>"; }).join("");
      intro.innerHTML = "<h3>" + esc(mock.title) + "</h3><p>" + mock.questions.length + " questions, " + mock.minutes + " minutes. " + mock.intro +
        "</p><ul class='plain'>" + mix + "</ul>";
      var go = document.createElement("button"); go.className = "btn primary"; go.textContent = "Start the " + mock.minutes + "-minute timer";
      go.addEventListener("click", function () {
        state.mockRun[key] = { started: Date.now(), deadline: Date.now() + mock.minutes * 60000, answers: {} }; save(); renderView();
      });
      intro.appendChild(go); seRoot.appendChild(intro);
      if (hist.length) renderMockResult(key, mock, hist[hist.length - 1], hist);
      return;
    }
    if (Date.now() >= run.deadline) { finishMock(key, mock, true); return; }
    var bar = document.createElement("div"); bar.className = "timer";
    bar.innerHTML = '<span class="clock" id="mock-clock"></span><span id="mock-answered"></span>';
    var sub = document.createElement("button"); sub.className = "btn primary"; sub.textContent = "Submit exam";
    sub.addEventListener("click", function () {
      if (confirm("Submit now? " + answeredCount(run) + " of " + mock.questions.length + " answered.")) finishMock(key, mock, false);
    });
    var ab = document.createElement("button"); ab.className = "btn"; ab.textContent = "Abandon";
    ab.addEventListener("click", function () { if (confirm("Abandon this attempt without scoring?")) { delete state.mockRun[key]; save(); renderView(); } });
    bar.appendChild(sub); bar.appendChild(ab); seRoot.appendChild(bar);
    function tick() {
      var left = (run.deadline - Date.now()) / 1000;
      var c = document.getElementById("mock-clock"); if (!c) { clearInterval(timerHandle); return; }
      c.textContent = fmt(left) + " left"; c.classList.toggle("low", left < 600);
      document.getElementById("mock-answered").textContent = answeredCount(run) + " / " + mock.questions.length + " answered";
      if (left <= 0) finishMock(key, mock, true);
    }
    var holder = document.createElement("div"); seRoot.appendChild(holder);
    renderList(holder, mock.questions, "mock",
      function (q) { return run.answers[q.id] || null; },
      function (q, r) { run.answers[q.id] = r; save(); },
      function () { return false; });
    tick(); timerHandle = setInterval(tick, 1000);
  }
  function renderMockResult(key, mock, res, hist) {
    var box = document.createElement("div"); box.className = "card";
    var ok = passed(mock, res.score);
    var rows = AREAS.filter(function (a) { return res.byArea[a.key]; }).map(function (a) {
      var x = res.byArea[a.key]; var p = Math.round(100 * x.right / x.total);
      return "<tr><td>" + esc(a.name) + "</td><td>" + x.right + " / " + x.total + "</td><td>" + p +
        '%</td><td><div class="bar' + (p < 70 ? " badbar" : "") + '"><div style="width:' + p + '%"></div></div></td></tr>';
    }).join("");
    var hrows = hist.map(function (h, i) {
      return "<tr><td>" + (i + 1) + "</td><td>" + esc(h.ts.replace("T", " ")) + "</td><td>" + h.score + mock.unit + "</td><td>" +
        (passed(mock, h.score) ? '<span class="ok">pass</span>' : '<span class="no">below pass</span>') + "</td><td>" + h.right + " / " + h.total + "</td><td>" + h.minutes + " min" + (h.auto ? " (time up)" : "") + "</td></tr>";
    }).join("");
    box.innerHTML = "<h3>Latest result</h3><p class='scorebox " + (ok ? "ok" : "no") + "'>" + res.score + mock.unit + " - " + (ok ? "PASS" : "BELOW PASS") +
      "</p><p>" + res.right + " of " + res.total + " correct in " + res.minutes + " minutes. Pass mark: " + mock.pass + mock.unit + ".</p>" +
      "<h4>By area</h4><table><tr><th>Area</th><th>Correct</th><th>%</th><th></th></tr>" + rows + "</table>" +
      "<h4>All attempts</h4><table><tr><th>#</th><th>When</th><th>Score</th><th></th><th>Correct</th><th>Time</th></tr>" + hrows + "</table>" +
      "<h4>Review: questions you missed (" + res.wrong.length + "), with explanations and docs links</h4>";
    seRoot.appendChild(box);
    var wrongQs = mock.questions.filter(function (q) { return res.wrong.indexOf(q.id) >= 0; });
    var holder = document.createElement("div"); seRoot.appendChild(holder);
    renderList(holder, wrongQs, "review",
      function (q) { return (res.answers || {})[q.id] || null; }, function () {}, function () { return true; });
    var all = document.createElement("details"); all.className = "case";
    all.innerHTML = "<summary>Review all " + mock.questions.length + " questions</summary>";
    var h2 = document.createElement("div"); all.appendChild(h2);
    all.addEventListener("toggle", function () {
      if (all.open && !h2.childNodes.length) renderList(h2, mock.questions, "reviewall",
        function (q) { return (res.answers || {})[q.id] || null; }, function () {}, function () { return true; });
    });
    seRoot.appendChild(all);
  }

  // ---------- scoreboard ----------
  function refreshScore() {
    var body = document.getElementById("sb-ex"); body.innerHTML = "";
    var cards = document.querySelectorAll(".page [data-ex]");
    var total = 0, passedN = 0, reqTotal = 0, reqPassed = 0;
    cards.forEach(function (c) {
      var id = c.dataset.ex; var gi = gradeInfo(id); var optional = !!c.querySelector(".tag.opt");
      total++; if (gi && gi.passed) passedN++;
      if (!optional) { reqTotal++; if (gi && gi.passed) reqPassed++; }
      var title = c.querySelector("h3").textContent; var typ = c.querySelector(".tag").textContent;
      var tr = document.createElement("tr");
      tr.innerHTML = '<td><a href="#' + c.id + '">' + esc(id) + "</a>" + (optional ? " (optional)" : "") + "</td><td>" + esc(title) + "</td><td>" + esc(typ) + "</td><td>" +
        (gi ? gi.latest : "-") + "</td><td>" + (gi ? gi.best : "-") + "</td><td>" +
        (gi ? (gi.passed ? '<span class="ok">pass</span>' : '<span class="no">retry</span>') : "not attempted") + "</td><td>" + (gi ? gi.attempts : 0) + "</td><td>" +
        (gi && gi.feedback ? '<a href="' + gi.feedback + '">latest</a>' : "") + "</td>";
      body.appendChild(tr);
    });
    var qb = document.getElementById("sb-quiz"); qb.innerHTML = "";
    var qTotal = 0, qChecked = 0;
    SETS.forEach(function (s) {
      var sc = setScore(s.list); qTotal += sc.total; qChecked += sc.answered;
      var tr = document.createElement("tr");
      tr.innerHTML = "<td>" + esc(s.label) + "</td><td>" + sc.right + " / " + sc.answered + "</td><td>" + sc.answered + " / " + sc.total +
        "</td><td>" + (sc.answered ? Math.round(100 * sc.right / sc.answered) + "%" : "-") + "</td>";
      qb.appendChild(tr);
    });
    var mb = document.getElementById("sb-mock"); mb.innerHTML = "";
    var mocksPassed = 0;
    MOCKS.forEach(function (m) {
      var hist = state.mock[m[0]] || [];
      var best = hist.reduce(function (acc, h) { return Math.max(acc, h.score); }, -1);
      if (best >= 0 && passed(m[1], best)) mocksPassed++;
      var last = hist.length ? hist[hist.length - 1] : null;
      var weakest = "";
      if (last) {
        var ws = Object.keys(last.byArea).map(function (k) { var x = last.byArea[k]; return [k, x.right / x.total]; }).sort(function (a, b) { return a[1] - b[1]; }).slice(0, 2);
        weakest = ws.map(function (w) { return esc(areaOf(w[0]).name) + " (" + Math.round(100 * w[1]) + "%)"; }).join(", ");
      }
      var tr = document.createElement("tr");
      tr.innerHTML = "<td>" + esc(m[1].title) + "</td><td>" + (last ? last.score + m[1].unit : "-") + "</td><td>" + (best >= 0 ? best + m[1].unit : "-") + "</td><td>" +
        (best >= 0 ? (passed(m[1], best) ? '<span class="ok">pass</span>' : '<span class="no">below pass</span>') : "not taken") + "</td><td>" + hist.length + "</td><td>" + weakest + "</td>";
      mb.appendChild(tr);
    });
    var pe = reqTotal ? reqPassed / reqTotal : 0, pq = qTotal ? qChecked / qTotal : 0, pm = MOCKS.length ? mocksPassed / MOCKS.length : 0;
    var overall = Math.round(100 * (pe + pq + pm) / 3);
    document.getElementById("sb-overall").innerHTML = "<b>" + overall + "% complete</b> - exercises passed " + reqPassed + " / " + reqTotal +
      " required (" + passedN + " / " + total + " incl. optional), quiz questions checked " + qChecked + " / " + qTotal + ", mock exams passed " + mocksPassed + " / " + MOCKS.length + ".";
    document.getElementById("bar-all").style.width = overall + "%";
    var ov = tabs.querySelector('[data-page="overview"] .pct'); if (ov) ov.textContent = overall + "%";
    pages.forEach(function (p) {
      var v = weekPct(p.id); if (v === null) return;
      var t = tabs.querySelector('[data-page="' + p.id + '"] .pct'); if (t) t.textContent = v + "%";
      var b = document.getElementById("bar-" + p.id); if (b) b.style.width = v + "%";
    });
  }

  buildNav(); renderView(); refreshScore(); show();
})();

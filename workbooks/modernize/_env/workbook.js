(function () {
  var KEY = "wb-modernize-v1";
  var PASS = 70;
  var D = window.MODERNIZE_DATA || { areas: [], weekly: [] };
  var state = {};
  try { state = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { state = {}; }
  state.q = state.q || {};
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

  var seRoot = document.getElementById("se-root");
  var seNav = document.getElementById("se-nav");
  var current = state.seView || "w1";
  function buildNav() {
    seNav.innerHTML = "";
    SETS.forEach(function (s) {
      var b = document.createElement("button"); b.textContent = s.label; b.dataset.view = s.key; seNav.appendChild(b);
    });
    seNav.querySelectorAll("button").forEach(function (b) {
      b.classList.toggle("active", b.dataset.view === current);
      b.addEventListener("click", function () { current = b.dataset.view; state.seView = current; save(); buildNav(); renderView(); });
    });
  }
  function renderView() {
    seRoot.innerHTML = "";
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
    var pe = reqTotal ? reqPassed / reqTotal : 0, pq = qTotal ? qChecked / qTotal : 0;
    var overall = Math.round(100 * (pe + pq) / 2);
    document.getElementById("sb-overall").innerHTML = "<b>" + overall + "% complete</b> - exercises passed " + reqPassed + " / " + reqTotal +
      " required (" + passedN + " / " + total + " incl. optional), quiz questions checked " + qChecked + " / " + qTotal + ".";
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

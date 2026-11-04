/* Steve's AI Guide — pick up where you left off.
   Remembers the section a reader reached in each guide (localStorage,
   this browser only, nothing sent anywhere) and uses it in three places:
   - guide pages: a 2px reading line across the top of the viewport, and a
     "Resume" link in the path rail when a saved position exists
   - homepage: "Continue · section N of M" on rows already started, a thin
     fill under the row, and the hero button pointing at the last guide read
   Self-injecting like sections.js: no per-page markup required. */
(function () {
  "use strict";

  var KEY = "sag:progress";
  var SCROLL_LINE = 120;          // same offset sections.js uses to pick the current section
  var MIN_SECTION_TO_RESUME = 1;  // index 0 is the first section; nothing to resume yet
  var page = location.pathname.split("/").pop() || "index.html";

  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }

  function load() {
    var data = {};
    try { data = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { data = {}; }
    return data;
  }
  function save(data) {
    try { localStorage.setItem(KEY, JSON.stringify(data)); } catch (e) { /* private mode, quota: the feature just stays off */ }
  }

  /* ---------- guide pages ---------- */

  function currentIndex(sections) {
    var y = window.pageYOffset, line = y + SCROLL_LINE, idx = -1;
    for (var k = 0; k < sections.length; k++) {
      if (sections[k].getBoundingClientRect().top + y <= line) idx = k; else break;
    }
    return idx;
  }

  function sectionTitle(sec) {
    var t = sec.querySelector(".accordion-title");
    return t ? t.textContent.replace(/#\s*$/, "").trim() : sec.id;
  }

  function remember(sections, idx) {
    if (idx < 0) return;
    var data = load();
    var prev = data[page] || {};
    var reached = Math.max(idx, prev.i || 0);
    data[page] = {
      i: reached,
      id: sections[reached].id,
      title: sectionTitle(sections[reached]),
      n: sections.length,
      done: reached === sections.length - 1,
      at: Date.now()
    };
    save(data);
  }

  function buildReadingLine() {
    var line = el("div", "sag-read-line");
    line.setAttribute("aria-hidden", "true");
    document.body.appendChild(line);
    return line;
  }

  function buildResume(rail, saved, sections) {
    if (!rail || !saved || saved.done || saved.i < MIN_SECTION_TO_RESUME || location.hash) return null;
    var target = document.getElementById(saved.id);
    if (!target) return null;
    var a = el("a", "sag-rail-resume", "Resume · section " + (saved.i + 1) + " of " + sections.length + " &rarr;");
    a.href = "#" + saved.id;
    a.title = saved.title;
    a.addEventListener("click", function () { a.remove(); });
    var next = rail.querySelector(".sag-rail-next");
    if (next) rail.insertBefore(a, next); else rail.appendChild(a);
    return a;
  }

  function guidePage(sections) {
    var article = sections[0].parentNode;
    var line = buildReadingLine();
    var saved = load()[page];
    var resume = buildResume(document.querySelector(".sag-rail-inner"), saved, sections);
    var last = -2, ticking = false;

    function update() {
      ticking = false;
      var idx = currentIndex(sections);
      var y = window.pageYOffset;
      var start = article.offsetTop, span = Math.max(1, article.offsetHeight - window.innerHeight);
      var frac = Math.min(1, Math.max(0, (y - start) / span));
      line.style.transform = "scaleX(" + frac.toFixed(4) + ")";
      if (idx !== last) {
        last = idx;
        remember(sections, idx);
        if (resume && saved && idx >= saved.i) { resume.remove(); resume = null; }
      }
    }
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* ---------- homepage ---------- */

  function rowFile(row) {
    var href = row.getAttribute("href") || "";
    return href.split("#")[0];
  }

  function decorateRow(row, saved) {
    var link = row.querySelector(".ramp-link");
    var foot = row.querySelector(".ramp-foot");
    if (!link) return;
    if (saved.done) {
      link.textContent = "Read again";
      row.classList.add("ramp-done");
    } else {
      link.textContent = "Continue · section " + (saved.i + 1) + " of " + saved.n;
      row.setAttribute("href", rowFile(row) + "#" + saved.id);
      row.classList.add("ramp-started");
    }
    var bar = el("span", "ramp-progress");
    bar.setAttribute("aria-hidden", "true");
    var pct = saved.done ? 100 : Math.round((saved.i / saved.n) * 100);
    bar.innerHTML = '<span style="width:' + pct + '%"></span>';
    (foot || row).appendChild(bar);
  }

  function pointHeroAt(row, saved) {
    var cta = document.querySelector(".hero .btn-primary");
    var title = row.querySelector(".ramp-title");
    if (!cta || !title) return;
    cta.setAttribute("href", rowFile(row) + "#" + saved.id);
    var svg = cta.querySelector("svg");
    cta.textContent = "Continue " + title.textContent.trim() + " ";
    if (svg) cta.appendChild(svg);
  }

  function homePage(rows) {
    var data = load(), latest = null, latestRow = null;
    rows.forEach(function (row) {
      var saved = data[rowFile(row)];
      if (!saved || saved.i < MIN_SECTION_TO_RESUME) return;
      decorateRow(row, saved);
      if (!saved.done && (!latest || saved.at > latest.at)) { latest = saved; latestRow = row; }
    });
    if (latestRow) pointHeroAt(latestRow, latest);
  }

  function init() {
    var sections = [].slice.call(document.querySelectorAll(".accordion[id]"));
    var rows = [].slice.call(document.querySelectorAll(".path-grid .ramp-card[href]"));
    if (sections.length) guidePage(sections);
    else if (rows.length) homePage(rows);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

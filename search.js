/* Steve's AI Guide — client-side search (static, no backend).
   Self-injects a search button + modal. Indexes search-index.json. */
(function () {
  "use strict";
  var idx = null, loading = false, sel = 0, results = [];

  var css = [
    ".wfs-btn{position:fixed;left:20px;bottom:20px;z-index:9998;display:inline-flex;align-items:center;gap:8px;",
    "padding:10px 16px;border-radius:9999px;background:var(--accent,#d4956a);color:#1a1410;font-weight:700;",
    "font-size:13px;border:none;cursor:pointer;box-shadow:0 6px 20px rgba(0,0,0,.4);font-family:inherit}",
    ".wfs-btn:hover{filter:brightness(1.06)}",
    ".wfs-btn kbd{background:rgba(26,20,16,.25);border-radius:4px;padding:1px 6px;font-size:11px;font-weight:700}",
    ".wfs-overlay{position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.6);backdrop-filter:blur(4px);",
    "display:none;align-items:flex-start;justify-content:center;padding:12vh 16px 16px}",
    ".wfs-overlay.open{display:flex}",
    ".wfs-modal{width:100%;max-width:640px;background:#15161a;border:1px solid #333;border-radius:14px;",
    "overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6);font-family:inherit}",
    ".wfs-inwrap{display:flex;align-items:center;gap:10px;padding:14px 18px;border-bottom:1px solid #2a2a2a}",
    ".wfs-inwrap svg{flex-shrink:0;color:var(--accent,#d4956a)}",
    ".wfs-input{flex:1;background:none;border:none;outline:none;color:#e8e8e8;font-size:17px;font-family:inherit}",
    ".wfs-input::placeholder{color:#888}",
    ".wfs-esc{font-size:11px;color:#888;border:1px solid #3a3a3a;border-radius:5px;padding:2px 7px}",
    ".wfs-results{max-height:56vh;overflow-y:auto;padding:6px}",
    ".wfs-item{display:block;padding:12px 14px;border-radius:9px;text-decoration:none;color:#e8e8e8}",
    ".wfs-item.sel,.wfs-item:hover{background:#22242b}",
    ".wfs-item .wfs-label{font-size:12px;color:var(--accent,#d4956a);font-weight:700;letter-spacing:.03em}",
    ".wfs-item .wfs-title{font-size:15px;font-weight:600;margin:2px 0}",
    ".wfs-item .wfs-snip{font-size:13px;color:#9a9a9a;line-height:1.5}",
    ".wfs-item .wfs-snip b{color:#cfcfcf}",
    ".wfs-empty{padding:28px 18px;text-align:center;color:#888;font-size:14px}",
    ".wfs-hint{padding:10px 16px;border-top:1px solid #2a2a2a;color:#777;font-size:11.5px;display:flex;gap:14px;flex-wrap:wrap}",
    "@media(max-width:520px){.wfs-btn kbd{display:none}}"
  ].join("");

  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function esc(s) { return s.replace(/[&<>]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]; }); }

  var overlay, input, list;
  function build() {
    var style = el("style"); style.textContent = css; document.head.appendChild(style);

    var btn = el("button", "wfs-btn");
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg> Search <kbd>/</kbd>';
    btn.setAttribute("aria-label", "Search the guides");
    btn.addEventListener("click", open);
    document.body.appendChild(btn);

    overlay = el("div", "wfs-overlay");
    overlay.innerHTML =
      '<div class="wfs-modal" role="dialog" aria-label="Search">' +
        '<div class="wfs-inwrap">' +
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>' +
          '<input class="wfs-input" type="text" placeholder="Search all seven guides…" aria-label="Search query" autocomplete="off" spellcheck="false">' +
          '<span class="wfs-esc">esc</span>' +
        '</div>' +
        '<div class="wfs-results"></div>' +
        '<div class="wfs-hint"><span><b>↑↓</b> navigate</span><span><b>↵</b> open</span><span><b>esc</b> close</span></div>' +
      '</div>';
    document.body.appendChild(overlay);
    input = overlay.querySelector(".wfs-input");
    list = overlay.querySelector(".wfs-results");

    overlay.addEventListener("click", function (e) { if (e.target === overlay) close(); });
    overlay.querySelector(".wfs-esc").addEventListener("click", close);
    input.addEventListener("input", run);
    input.addEventListener("keydown", onKey);
  }

  function load() {
    if (idx || loading) return;
    loading = true;
    fetch("search-index.json").then(function (r) { return r.json(); }).then(function (d) { idx = d; run(); })
      .catch(function () { list.innerHTML = '<div class="wfs-empty">Search index could not load.</div>'; });
  }

  function open() { overlay.classList.add("open"); document.body.style.overflow = "hidden"; input.focus(); input.select(); load(); if (idx) run(); }
  function close() { overlay.classList.remove("open"); document.body.style.overflow = ""; }

  function snippet(page, q) {
    var t = page.text, i = t.indexOf(q.toLowerCase());
    if (i < 0) {
      var hh = page.headings.find(function (h) { return h.toLowerCase().indexOf(q.toLowerCase()) >= 0; });
      if (hh) return esc(hh);
      return esc(page.desc || page.headings.slice(0, 2).join(" · "));
    }
    var start = Math.max(0, i - 40), seg = t.slice(start, i + q.length + 60);
    seg = (start > 0 ? "…" : "") + seg + "…";
    var re = new RegExp("(" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
    return esc(seg).replace(re, "<b>$1</b>");
  }

  function score(page, terms, raw) {
    var s = 0, L = (page.label + " " + page.title).toLowerCase(), H = page.headings.join(" ").toLowerCase(), T = page.text;
    terms.forEach(function (t) {
      if (L.indexOf(t) >= 0) s += 12;
      if (H.indexOf(t) >= 0) s += 5;
      if (T.indexOf(t) >= 0) s += 2;
    });
    if (L.indexOf(raw) >= 0) s += 8;
    if (H.indexOf(raw) >= 0) s += 4;
    return s;
  }

  function run() {
    if (!idx) { load(); return; }
    var raw = input.value.trim().toLowerCase();
    if (!raw) {
      results = idx.slice();
      list.innerHTML = '<div class="wfs-empty">Type to search 7 guides, workflows, and plugin docs.</div>';
      return;
    }
    var terms = raw.split(/\s+/);
    results = idx.map(function (p) { return { p: p, s: score(p, terms, raw) }; })
      .filter(function (x) { return x.s > 0; })
      .sort(function (a, b) { return b.s - a.s; })
      .slice(0, 8).map(function (x) { return x.p; });
    sel = 0;
    render(raw);
  }

  function render(raw) {
    if (!results.length) { list.innerHTML = '<div class="wfs-empty">No matches for “' + esc(raw) + '”.</div>'; return; }
    list.innerHTML = results.map(function (p, i) {
      var kind = p.url === "index.html" ? "Home" : (/linkedin|follow-up/.test(p.url) ? "Plugin" : "Guide");
      return '<a class="wfs-item' + (i === sel ? " sel" : "") + '" href="' + p.url + '">' +
        '<span class="wfs-label">' + kind + '</span>' +
        '<div class="wfs-title">' + esc(p.label) + '</div>' +
        '<div class="wfs-snip">' + snippet(p, raw) + '</div></a>';
    }).join("");
  }

  function onKey(e) {
    if (e.key === "Escape") { close(); }
    else if (e.key === "ArrowDown") { e.preventDefault(); sel = Math.min(sel + 1, results.length - 1); render(input.value.trim().toLowerCase()); scrollSel(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); sel = Math.max(sel - 1, 0); render(input.value.trim().toLowerCase()); scrollSel(); }
    else if (e.key === "Enter") { if (results[sel]) window.location.href = results[sel].url; }
  }
  function scrollSel() { var n = list.querySelector(".wfs-item.sel"); if (n) n.scrollIntoView({ block: "nearest" }); }

  document.addEventListener("keydown", function (e) {
    var tag = (document.activeElement && document.activeElement.tagName) || "";
    var typing = tag === "INPUT" || tag === "TEXTAREA";
    if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) { e.preventDefault(); open(); }
    else if (e.key === "/" && !typing && !overlay.classList.contains("open")) { e.preventDefault(); open(); }
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build);
  else build();
})();

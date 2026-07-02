/* Steve's AI Guide — open-section navigation.
   Replaces the retired accordion JS (2026-07). Sections are always open;
   this script provides orientation instead of concealment:
   - sticky-nav scroll-spy ("Step N of M · Title") with a tap-to-jump menu
   - URL hash tracking via history.replaceState (shareable section links)
   - hover anchor links on section headings
   - back-to-top button
   Self-injecting like search.js: no per-page markup required beyond
   #stickyNav / #stickyProgress (optional) and .accordion sections. */
(function () {
  "use strict";

  var sections = [], labels = [], current = -2; // -2 = unrendered, so the initial -1 (above first section) state paints
  var stickyNav, stickyProgress, jumpMenu, jumpOpen = false;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  var css = [
    ".sec-anchor{opacity:0;margin-left:10px;font-size:17px;font-weight:400;text-decoration:none;",
    "color:var(--accent,#d4956a);transition:opacity .15s;vertical-align:middle}",
    "h2.accordion-title:hover .sec-anchor,.sec-anchor:focus{opacity:1}",
    "#stickyProgress{cursor:pointer;user-select:none;display:inline-flex;align-items:center;gap:6px;",
    "max-width:60vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}",
    "#stickyProgress .sg-caret{font-size:9px;opacity:.7}",
    ".sg-jump{position:fixed;top:52px;right:16px;z-index:9997;min-width:260px;max-width:88vw;max-height:60vh;",
    "overflow-y:auto;background:#15161a;border:1px solid #333;border-radius:12px;padding:6px;",
    "box-shadow:0 20px 60px rgba(0,0,0,.55);display:none}",
    ".sg-jump.open{display:block}",
    ".sg-jump a{display:flex;gap:10px;align-items:baseline;padding:9px 12px;border-radius:8px;",
    "text-decoration:none;color:#d8d8d8;font-size:13.5px;line-height:1.35}",
    ".sg-jump a:hover{background:#22242b}",
    ".sg-jump a.current{color:var(--accent,#d4956a);font-weight:700}",
    ".sg-jump a .sg-n{color:var(--accent,#d4956a);font-size:11px;font-weight:700;min-width:16px}",
    ".sg-top{position:fixed;right:20px;bottom:74px;z-index:9996;width:42px;height:42px;border-radius:50%;",
    "background:#22242b;color:#e8e8e8;border:1px solid #3a3a3a;font-size:18px;cursor:pointer;",
    "opacity:0;pointer-events:none;transition:opacity .2s;box-shadow:0 6px 20px rgba(0,0,0,.4)}",
    ".sg-top.visible{opacity:1;pointer-events:auto}",
    ".sg-top:hover{filter:brightness(1.2)}"
  ].join("");

  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function scrollBehavior() { return reduceMotion.matches ? "auto" : "smooth"; }

  function sectionLabel(sec) {
    var lab = sec.querySelector(".accordion-label");
    var tit = sec.querySelector(".accordion-title");
    return {
      label: lab ? lab.textContent.trim() : "",
      title: tit ? tit.textContent.replace(/#\s*$/, "").trim() : sec.id
    };
  }

  function buildAnchors() {
    sections.forEach(function (sec) {
      var h = sec.querySelector("h2.accordion-title");
      if (!h) return;
      var a = el("a", "sec-anchor", "#");
      a.href = "#" + sec.id;
      a.setAttribute("aria-label", "Link to this section");
      h.appendChild(a);
    });
  }

  function buildJumpMenu() {
    if (!stickyProgress) return;
    jumpMenu = el("nav", "sg-jump");
    jumpMenu.setAttribute("aria-label", "Jump to section");
    jumpMenu.innerHTML = sections.map(function (sec, i) {
      var m = labels[i];
      return '<a href="#' + sec.id + '" data-i="' + i + '"><span class="sg-n">' + (i + 1) + '</span>' + m.title + "</a>";
    }).join("");
    document.body.appendChild(jumpMenu);

    stickyProgress.setAttribute("role", "button");
    stickyProgress.setAttribute("tabindex", "0");
    stickyProgress.setAttribute("aria-expanded", "false");
    stickyProgress.addEventListener("click", toggleJump);
    stickyProgress.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleJump(); }
    });
    jumpMenu.addEventListener("click", function () { setJump(false); });
    document.addEventListener("click", function (e) {
      if (jumpOpen && !jumpMenu.contains(e.target) && e.target !== stickyProgress && !stickyProgress.contains(e.target)) setJump(false);
    });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setJump(false); });
  }

  function toggleJump() { setJump(!jumpOpen); }
  function setJump(open) {
    jumpOpen = open;
    if (jumpMenu) jumpMenu.classList.toggle("open", open);
    if (stickyProgress) stickyProgress.setAttribute("aria-expanded", String(open));
  }

  function buildBackToTop() {
    var b = el("button", "sg-top", "↑");
    b.setAttribute("aria-label", "Back to top");
    b.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: scrollBehavior() }); });
    document.body.appendChild(b);
    return b;
  }

  function bindAnchorScroll() {
    // Smooth-scroll in-page anchor clicks (TOC, jump menu, heading links).
    // Deliberately not CSS html{scroll-behavior:smooth}: that would animate
    // the browser's on-load fragment scroll too, which crawls or stalls on
    // long pages. Fresh loads with a hash stay native and instant.
    document.addEventListener("click", function (e) {
      var a = e.target.closest ? e.target.closest('a[href^="#"]') : null;
      if (!a) return;
      var target = document.getElementById(a.getAttribute("href").slice(1));
      if (!target) return;
      e.preventDefault();
      history.pushState(null, "", a.getAttribute("href"));
      target.scrollIntoView({ behavior: scrollBehavior(), block: "start" });
    });
  }

  function reanchorAfterLoad() {
    // Images on the guide pages have no fixed dimensions, so layout grows
    // during load and the browser's fragment scroll can land far from the
    // target (or not fire at all in throttled tabs). Once everything has
    // loaded, snap to the hash target if it drifted out of view.
    window.addEventListener("load", function () {
      if (!window.location.hash) return;
      var t = document.getElementById(window.location.hash.slice(1));
      if (t && Math.abs(t.getBoundingClientRect().top) > window.innerHeight) {
        t.scrollIntoView({ behavior: "auto", block: "start" });
      }
    });
  }

  function bindHeroCta() {
    var cta = document.getElementById("heroCtaBtn");
    if (!cta || !sections.length) return;
    cta.addEventListener("click", function (e) {
      e.preventDefault();
      sections[0].scrollIntoView({ behavior: scrollBehavior(), block: "start" });
    });
  }

  function setCurrent(i) {
    if (i === current) return;
    current = i;
    sections.forEach(function (sec, k) {
      var h = sec.querySelector(".accordion-header");
      if (h) h.classList.toggle("open", k === i);
    });
    if (jumpMenu) [].forEach.call(jumpMenu.querySelectorAll("a"), function (a, k) {
      a.classList.toggle("current", k === i);
    });
    if (stickyProgress) {
      if (i >= 0) {
        var m = labels[i];
        var prefix = m.label ? m.label + " of " + sections.length : (i + 1) + " of " + sections.length;
        stickyProgress.innerHTML = prefix + " · " + m.title + ' <span class="sg-caret">▼</span>';
      } else {
        stickyProgress.innerHTML = sections.length + " sections · jump ▾";
      }
    }
    // Deliberately no history.replaceState here: rewriting the hash on scroll
    // races the browser's own fragment navigation on load and clobbers
    // standalone anchors like workflows.html#reliability. The hash changes
    // only via real anchor navigation (TOC, jump menu, heading links).
  }

  function watchScroll(topBtn) {
    var ticking = false;
    function update() {
      ticking = false;
      var y = window.pageYOffset;
      var line = y + 120;
      var idx = -1;
      for (var k = 0; k < sections.length; k++) {
        if (sections[k].getBoundingClientRect().top + y <= line) idx = k; else break;
      }
      setCurrent(idx);
      if (stickyNav) stickyNav.classList.toggle("visible", sections.length && y > sections[0].getBoundingClientRect().top + y - window.innerHeight * 0.6);
      if (topBtn) topBtn.classList.toggle("visible", y > 500);
      if (jumpOpen && y !== lastY) setJump(false);
      lastY = y;
    }
    var lastY = window.pageYOffset;
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  function init() {
    sections = [].slice.call(document.querySelectorAll(".accordion[id]"));
    if (!sections.length) return;
    labels = sections.map(sectionLabel);
    stickyNav = document.getElementById("stickyNav");
    stickyProgress = document.getElementById("stickyProgress");

    var style = el("style"); style.textContent = css; document.head.appendChild(style);
    buildAnchors();
    buildJumpMenu();
    bindAnchorScroll();
    reanchorAfterLoad();
    bindHeroCta();
    watchScroll(buildBackToTop());
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

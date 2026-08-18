/* Steve's AI Guide — unified navigation behavior.
   Markup is injected statically by build-nav.py, so the nav renders without
   JS. This file only adds the interactive layer: dropdowns, the mobile
   sheet, and handing search off to search.js (which already owns Cmd/Ctrl+K). */
(function () {
  "use strict";

  var nav = document.querySelector(".sag-nav");
  if (!nav) return;

  document.body.classList.add("sag-has-nav");

  /* ---- dropdowns (click to open; hover is a desktop-only nicety) ---- */
  var dds = [].slice.call(nav.querySelectorAll(".sag-dd"));

  function closeAll(except) {
    dds.forEach(function (dd) {
      if (dd === except) return;
      dd.classList.remove("open");
      var b = dd.querySelector(".sag-dd-btn");
      if (b) b.setAttribute("aria-expanded", "false");
    });
  }

  dds.forEach(function (dd) {
    var btn = dd.querySelector(".sag-dd-btn");
    if (!btn) return;
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      var willOpen = !dd.classList.contains("open");
      closeAll(dd);
      dd.classList.toggle("open", willOpen);
      btn.setAttribute("aria-expanded", willOpen ? "true" : "false");
    });
  });

  document.addEventListener("click", function (e) {
    if (!nav.contains(e.target)) closeAll();
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { closeAll(); closeSheet(); }
  });

  /* ---- mobile sheet ---- */
  var burger = document.getElementById("sagBurger");
  var sheet = document.getElementById("sagSheet");

  function closeSheet() {
    if (!sheet) return;
    sheet.classList.remove("open");
    document.body.style.overflow = "";
    if (burger) burger.setAttribute("aria-expanded", "false");
  }

  if (burger && sheet) {
    burger.addEventListener("click", function () {
      var willOpen = !sheet.classList.contains("open");
      sheet.classList.toggle("open", willOpen);
      document.body.style.overflow = willOpen ? "hidden" : "";
      burger.setAttribute("aria-expanded", willOpen ? "true" : "false");
    });
    // Same-page anchors need the sheet out of the way to reveal the target.
    sheet.addEventListener("click", function (e) {
      if (e.target.closest("a")) closeSheet();
    });
  }

  // A resize past the breakpoint must not strand a locked <body>.
  window.addEventListener("resize", function () {
    if (window.innerWidth > 900) closeSheet();
  });

  /* ---- search: search.js owns the modal and the Cmd/Ctrl+K binding.
         Its floating pill is hidden by nav.css; forward the click instead. ---- */
  function openSearch() {
    var pill = document.querySelector(".wfs-btn");
    if (pill) { pill.click(); return; }
    // search.js builds on DOMContentLoaded; retry once if we beat it there.
    setTimeout(function () {
      var late = document.querySelector(".wfs-btn");
      if (late) late.click();
    }, 250);
  }

  [].slice.call(document.querySelectorAll(".sag-search, .sag-sheet-search"))
    .forEach(function (b) { b.addEventListener("click", openSearch); });
})();

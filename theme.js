// Theme toggle. The stylesheet already follows prefers-color-scheme; this only
// records an explicit choice as data-theme on <html>, which overrides it.
// The no-flash part lives inline in each page's <head> -- it has to run before
// first paint, which a deferred external file cannot.
(function () {
  var root = document.documentElement;
  var btn = document.getElementById("theme-toggle");
  if (!btn) return;

  var media = window.matchMedia("(prefers-color-scheme: dark)");

  function current() {
    return root.getAttribute("data-theme") || (media.matches ? "dark" : "light");
  }

  function relabel() {
    btn.setAttribute("aria-label",
      current() === "dark" ? "Switch to light theme" : "Switch to dark theme");
  }

  btn.addEventListener("click", function () {
    var next = current() === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) { /* private mode */ }
    relabel();
  });

  if (media.addEventListener) media.addEventListener("change", relabel);
  relabel();
})();

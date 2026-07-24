// Live GitHub star counts - progressive enhancement.
// Adds a small "★ N" pill to any <a data-repo="owner/name"> when the repo
// has at least one star. Fails silently (e.g. offline or rate-limited).
(function () {
  var links = document.querySelectorAll("a[data-repo]");
  links.forEach(function (a) {
    var repo = a.getAttribute("data-repo");
    fetch("https://api.github.com/repos/" + repo)
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (d) {
        if (d && typeof d.stargazers_count === "number" && d.stargazers_count > 0) {
          var s = document.createElement("span");
          s.className = "stars";
          s.setAttribute("aria-label", d.stargazers_count + " stars on GitHub");
          s.textContent = "★ " + d.stargazers_count;
          a.appendChild(s);
        }
      })
      .catch(function () {});
  });
})();

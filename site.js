// Shared helpers for the blog. Posts are markdown files in /posts,
// indexed in posts/posts.json. No build step — everything renders in the browser.

async function loadIndex() {
  const res = await fetch("posts/posts.json", { cache: "no-store" });
  if (!res.ok) throw new Error("Could not load posts.json");
  const posts = await res.json();
  // newest first by date string (YYYY-MM-DD sorts correctly)
  return posts.sort((a, b) => (a.date < b.date ? 1 : -1));
}

function fmtDate(iso) {
  const d = new Date(iso + "T00:00:00");
  if (isNaN(d)) return iso;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
}

// ---- blog.html: render the list ----
async function renderList(elId) {
  const el = document.getElementById(elId);
  try {
    const posts = await loadIndex();
    if (!posts.length) {
      el.innerHTML = '<p class="empty">No posts yet. Add your first one in the posts/ folder.</p>';
      return;
    }
    el.innerHTML = posts.map(p => `
      <a class="post-link" href="post.html?p=${encodeURIComponent(p.file)}">
        <span class="post-date">${fmtDate(p.date)}</span>
        <div class="post-title">${escapeHtml(p.title)}</div>
        ${p.excerpt ? `<p class="post-excerpt">${escapeHtml(p.excerpt)}</p>` : ""}
      </a>`).join("");
  } catch (e) {
    el.innerHTML = '<p class="empty">Couldn\'t load posts. If you\'re opening this file locally, host it on GitHub Pages instead — browsers block local file fetches.</p>';
  }
}

// ---- post.html: render a single post ----
async function renderPost(elId) {
  const el = document.getElementById(elId);
  const params = new URLSearchParams(location.search);
  const file = params.get("p");
  if (!file || /[^a-zA-Z0-9._-]/.test(file)) {
    el.innerHTML = '<p class="empty">Post not found.</p>';
    return;
  }
  try {
    const index = await loadIndex();
    const meta = index.find(p => p.file === file) || {};
    const res = await fetch("posts/" + file, { cache: "no-store" });
    if (!res.ok) throw new Error("missing");
    const md = await res.text();
    const html = marked.parse(md);
    document.title = (meta.title || "Post") + " — Blog";
    el.innerHTML = `
      ${meta.date ? `<span class="post-date">${fmtDate(meta.date)}</span>` : ""}
      ${html}`;
  } catch (e) {
    el.innerHTML = '<p class="empty">Couldn\'t load this post.</p>';
  }
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

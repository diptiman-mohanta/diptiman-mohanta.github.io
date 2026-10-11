#!/usr/bin/env python3
"""Render publications.json into the marked region of index.html.

No build step for the site itself -- this is a one-shot generator run locally or
by .github/workflows/publications.yml. It only ever touches the text between the
PUBS markers, and it refuses to write anything it isn't sure about.

Usage:
  python tools/build_pubs.py          # rewrite index.html if the region changed
  python tools/build_pubs.py --check  # exit 1 if it would change (for CI)
"""
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "publications.json"
PAGE = ROOT / "index.html"

START = "    <!-- PUBS:START (generated from publications.json by tools/build_pubs.py) -->"
END = "    <!-- PUBS:END -->"


def esc(text):
    """Escape a text node. Quotes are left alone -- they are safe in element
    content and &#x27; in a prose sentence is noise in the page source."""
    return html.escape(str(text), quote=False)


def render(pubs):
    out = [START]
    for n, p in enumerate(pubs, 1):
        venue = esc(p["venue"])
        if p.get("venue_italic"):
            venue = f"<em>{venue}</em>"
        links = "".join(
            '<a href="{url}"{repo}>{label}</a>'.format(
                url=html.escape(l["url"]),
                repo=' data-repo="%s"' % html.escape(l["repo"]) if l.get("repo") else "",
                label=esc(l["label"]),
            )
            for l in p.get("links", [])
        )
        out.append('')
        out.append('    <article class="pub">')
        out.append('      <span class="pub-no">%02d</span>' % n)
        out.append('      <div>')
        out.append('        <h3 class="pub-title">%s</h3>' % esc(p["title"]))
        # authors is trusted markup: it carries the <strong> around his own name
        out.append('        <p class="pub-venue">%s · %s, %s</p>'
                   % (p["authors"], venue, esc(p["year"])))
        if p.get("note"):
            out.append('        <p class="pub-note">%s</p>' % esc(p["note"]))
        if links:
            out.append('        <p class="pub-links">%s</p>' % links)
        out.append('      </div>')
        out.append('    </article>')
    out.append('')
    out.append(END)
    return "\n".join(out)


def main():
    pubs = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(pubs, list) or not pubs:
        sys.exit("publications.json is empty or not a list -- refusing to write")
    for i, p in enumerate(pubs):
        for field in ("title", "authors", "venue", "year"):
            if not p.get(field):
                sys.exit("entry %d is missing %r -- refusing to write" % (i, field))
    # newest first
    pubs.sort(key=lambda p: (p.get("date") or str(p["year"])), reverse=True)

    page = PAGE.read_text(encoding="utf-8")
    if page.count(START) != 1 or page.count(END) != 1:
        sys.exit("index.html must contain exactly one PUBS:START and one PUBS:END marker")
    head, rest = page.split(START, 1)
    _, tail = rest.split(END, 1)
    new_page = head + render(pubs) + tail

    if new_page == page:
        print("publications section already up to date (%d entries)" % len(pubs))
        return
    if "--check" in sys.argv:
        sys.exit("index.html is out of date -- run: python tools/build_pubs.py")
    PAGE.write_text(new_page, encoding="utf-8")
    print("rewrote publications section (%d entries)" % len(pubs))


if __name__ == "__main__":
    main()

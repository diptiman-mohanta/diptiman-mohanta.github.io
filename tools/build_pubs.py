#!/usr/bin/env python3
"""Render publications.json into the marked regions of index.html.

No build step for the site itself -- this is a one-shot generator run locally or
by .github/workflows/publications.yml. It only ever touches the text between the
PUBS markers, and it refuses to write anything it isn't sure about.

Entries are grouped by their "type" field, in GROUPS order. A group with no
entries is left out of the page entirely, and each group numbers its own
entries from one.

Usage:
  python tools/build_pubs.py          # rewrite index.html if the regions changed
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
COUNT_START = "<!-- PUBCOUNT:START -->"
COUNT_END = "<!-- PUBCOUNT:END -->"

# (type in publications.json, heading on the page), in the order they appear.
GROUPS = [
    ("journal", "Journals"),
    ("conference", "Selected Conferences"),
    ("preprint", "Submitted / arXiv"),
    ("magazine", "Magazines"),
]
TYPES = {t for t, _ in GROUPS}


def esc(text):
    """Escape a text node. Quotes are left alone -- they are safe in element
    content and &#x27; in a prose sentence is noise in the page source."""
    return html.escape(str(text), quote=False)


def rich(text):
    """Same, plus **bold**. Escaping happens first, so the only markup that can
    reach the page is the <strong> this function puts there itself."""
    out = esc(text)
    while out.count("**") >= 2:
        out = out.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
    return out


def render_entry(n, p):
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
    out = []
    out.append('      <article class="pub">')
    out.append('        <span class="pub-no">%02d</span>' % n)
    out.append('        <div>')
    out.append('          <h3 class="pub-title">%s</h3>' % esc(p["title"]))
    # authors is trusted markup: it carries the <strong> around his own name
    out.append('          <p class="pub-venue">%s · %s, %s</p>'
               % (p["authors"], venue, esc(p["year"])))
    if p.get("note"):
        out.append('          <p class="pub-note">%s</p>' % rich(p["note"]))
    if links:
        out.append('          <p class="pub-links">%s</p>' % links)
    out.append('        </div>')
    out.append('      </article>')
    return out


def render(pubs):
    out = [START]
    for kind, heading in GROUPS:
        entries = [p for p in pubs if p["type"] == kind]
        if not entries:
            continue  # a group with nothing in it does not appear at all
        out.append('')
        out.append('    <div class="pub-group">')
        out.append('      <h3 class="subhead">%s <span class="count">(%d)</span></h3>'
                   % (esc(heading), len(entries)))
        for n, p in enumerate(entries, 1):
            out.extend(render_entry(n, p))
        out.append('    </div>')
    out.append('')
    out.append(END)
    return "\n".join(out)


def main():
    pubs = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(pubs, list) or not pubs:
        sys.exit("publications.json is empty or not a list -- refusing to write")
    for i, p in enumerate(pubs):
        for field in ("title", "authors", "venue", "year", "type"):
            if not p.get(field):
                sys.exit("entry %d is missing %r -- refusing to write" % (i, field))
        if p["type"] not in TYPES:
            sys.exit("entry %d has unknown type %r -- expected one of %s"
                     % (i, p["type"], ", ".join(sorted(TYPES))))
    # newest first
    pubs.sort(key=lambda p: (p.get("date") or str(p["year"])), reverse=True)

    page = PAGE.read_text(encoding="utf-8")
    for marker in (START, END, COUNT_START, COUNT_END):
        if page.count(marker) != 1:
            sys.exit("index.html must contain exactly one %s" % marker.strip())

    head, rest = page.split(START, 1)
    _, tail = rest.split(END, 1)
    new_page = head + render(pubs) + tail

    # the total next to the section heading
    before, rest = new_page.split(COUNT_START, 1)
    _, after = rest.split(COUNT_END, 1)
    new_page = before + COUNT_START + str(len(pubs)) + COUNT_END + after

    if new_page == page:
        print("publications section already up to date (%d entries)" % len(pubs))
        return
    if "--check" in sys.argv:
        sys.exit("index.html is out of date -- run: python tools/build_pubs.py")
    PAGE.write_text(new_page, encoding="utf-8")
    counts = ", ".join("%s %d" % (h, len([p for p in pubs if p["type"] == t]))
                       for t, h in GROUPS if any(p["type"] == t for p in pubs))
    print("rewrote publications section (%d entries: %s)" % (len(pubs), counts))


if __name__ == "__main__":
    main()

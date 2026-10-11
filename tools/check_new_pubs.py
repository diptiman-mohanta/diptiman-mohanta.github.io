#!/usr/bin/env python3
"""Ask ORCID whether there are works that publications.json doesn't list yet.

ORCID is the source we poll because it's an official, stable, keyless JSON API --
unlike Google Scholar, which has no API and blocks CI runners with CAPTCHAs.
arXiv and most publishers can push new works into an ORCID record automatically,
so in practice a new paper shows up here without any manual step.

Prints a markdown summary of anything missing and exits 2, so the workflow can
open an issue. Exits 0 when nothing is new, and 0 on network failure too -- a
flaky API should never look like a finding.
"""
import json
import pathlib
import sys
import urllib.error
import urllib.request

ORCID = "0009-0001-4744-8465"
API = "https://pub.orcid.org/v3.0/%s/works" % ORCID
ROOT = pathlib.Path(__file__).resolve().parent.parent


def norm(s):
    return "".join(c for c in str(s).lower() if c.isalnum())


def main():
    known = json.loads((ROOT / "publications.json").read_text(encoding="utf-8"))
    seen = set()
    for p in known:
        seen.add(norm(p["title"]))
        if p.get("orcid_id"):
            seen.add(norm(p["orcid_id"]))

    req = urllib.request.Request(API, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print("could not reach ORCID (%s) -- treating as 'nothing new'" % e)
        return 0

    groups = data.get("group") or []
    if not groups:
        print("ORCID returned no works -- treating as 'nothing new'")
        return 0

    new = []
    for g in groups:
        summary = (g.get("work-summary") or [{}])[0]
        title = (((summary.get("title") or {}).get("title") or {}).get("value") or "").strip()
        ids = [i.get("external-id-value", "") for i in
               ((g.get("external-ids") or {}).get("external-id") or [])]
        urls = [i.get("external-id-url", {}).get("value", "") for i in
                ((g.get("external-ids") or {}).get("external-id") or []) if i.get("external-id-url")]
        if norm(title) in seen or any(norm(i) in seen for i in ids if i):
            continue
        journal = (summary.get("journal-title") or {}).get("value") or ""
        year = (((summary.get("publication-date") or {}).get("year") or {}).get("value") or "")
        new.append({"title": title, "journal": journal, "year": year,
                    "ids": [i for i in ids if i], "urls": urls})

    if not new:
        print("no new works (%d on ORCID, %d in publications.json)" % (len(groups), len(known)))
        return 0

    print("Found %d work(s) on ORCID that aren't in `publications.json` yet:\n" % len(new))
    for w in new:
        print("### %s" % (w["title"] or "(untitled)"))
        if w["journal"]:
            print("- Venue: %s" % w["journal"])
        if w["year"]:
            print("- Year: %s" % w["year"])
        for i in w["ids"]:
            print("- ID: `%s`" % i)
        for u in w["urls"]:
            print("- %s" % u)
        print()
    print("To publish it: add an entry to `publications.json` "
          "(copy the shape of an existing one -- `authors` is the only field that "
          "takes HTML, for the `<strong>` around your own name), then push. "
          "The workflow regenerates the page and closes this issue's reason to exist.")
    return 2


if __name__ == "__main__":
    sys.exit(main())

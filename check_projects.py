#!/usr/bin/env python3
"""Check Drupal.org projects against the CivicActions maintenance lifecycle recommendations.

Criteria (see drupal-project-maintenance-lifecycle.md):
  1. CivicActions is a supporting organization with a recommended attribution line.
  2. The 'civicactions' user is listed as a maintainer.

Usage:
  ./check_projects.py dkan_ai_query ai_revision_log
  ./check_projects.py https://www.drupal.org/project/dkan_ai_query

Exit code is 0 when every project passes both criteria, 1 otherwise, 2 on fetch errors.
"""
import argparse
import re
import sys
import urllib.error
import urllib.request
from html import unescape

BASE_URL = "https://www.drupal.org/project/"
ORG_SLUG = "civicactions"
MAINTAINER_USER = "civicactions"
RECOMMENDED_ATTRIBUTIONS = {
    "development and ideation",
    "provides time and technical support",
    "provided time for community contribution",
}

# Drupal.org serves a JavaScript bot challenge to browser-like user agents;
# a plain curl-style agent gets the real page.
USER_AGENT = "curl/8"

ORG_ITEM_SPLIT = re.compile(
    r'<div class="entity entity-field-collection-item '
    r'field-collection-item-field-supporting-organizations'
)
ORG_LINK = re.compile(
    r'field-name-field-supporting-organization .*?<a href="/([^"]+)">([^<]*)</a>', re.S
)
HOW_HELPED = re.compile(
    r'field-name-field-how-they-helped .*?<div class="field-item[^"]*">(.*?)</div>', re.S
)
MAINTAINER_LINK = re.compile(r'<div class="maintainer">.*?<small><a href="/u/([^"]+)">', re.S)


def machine_name(arg):
    return arg.rstrip("/").rsplit("/", 1)[-1]


def fetch(name):
    req = urllib.request.Request(BASE_URL + name, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_supporting_orgs(html):
    """Return a list of (org_slug, attribution) tuples; attribution is '' when blank."""
    orgs = []
    for chunk in ORG_ITEM_SPLIT.split(html)[1:]:
        chunk = chunk.split("\n</div>", 1)[0]
        org = ORG_LINK.search(chunk)
        if not org:
            continue
        helped = HOW_HELPED.search(chunk)
        text = unescape(re.sub(r"<[^>]+>", "", helped.group(1))).strip() if helped else ""
        orgs.append((org.group(1), text))
    return orgs


def parse_maintainers(html):
    return [unescape(m) for m in MAINTAINER_LINK.findall(html)]


def check(name):
    html = fetch(name)
    if "block-drupalorg-project-maintainers" not in html:
        raise RuntimeError("unexpected page content (not a project page or blocked)")

    attribution = next((a for slug, a in parse_supporting_orgs(html) if slug == ORG_SLUG), None)
    maintainers = parse_maintainers(html)

    if attribution is None:
        attribution_note = "CivicActions not listed as a supporting organization"
    elif attribution.lower() in RECOMMENDED_ATTRIBUTIONS:
        attribution_note = f'"{attribution}"'
    else:
        attribution_note = f'"{attribution}" is not a recommended attribution line' if attribution else "attribution line is blank"

    return {
        "attribution_ok": attribution is not None and attribution.lower() in RECOMMENDED_ATTRIBUTIONS,
        "attribution_note": attribution_note,
        "maintainer_ok": MAINTAINER_USER in (m.lower() for m in maintainers),
        "maintainers": maintainers,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("projects", nargs="+", help="Project machine names or drupal.org project URLs")
    args = parser.parse_args()

    all_pass, errors = True, False
    for arg in args.projects:
        name = machine_name(arg)
        try:
            r = check(name)
        except (urllib.error.URLError, RuntimeError) as e:
            print(f"{name}: ERROR {e}", file=sys.stderr)
            errors = True
            continue
        ok = r["attribution_ok"] and r["maintainer_ok"]
        all_pass &= ok
        print(f"{name}: {'PASS' if ok else 'FAIL'}")
        print(f"  attribution line: {'OK' if r['attribution_ok'] else 'FAIL'} - {r['attribution_note']}")
        print(f"  '{MAINTAINER_USER}' maintainer: {'OK' if r['maintainer_ok'] else 'FAIL'} "
              f"(maintainers: {', '.join(r['maintainers']) or 'none found'})")

    return 2 if errors else (0 if all_pass else 1)


if __name__ == "__main__":
    sys.exit(main())

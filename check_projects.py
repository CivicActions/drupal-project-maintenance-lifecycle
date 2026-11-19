#!/usr/bin/env python3
"""Check Drupal.org projects against the CivicActions maintenance lifecycle recommendations.

Criteria (see drupal-project-maintenance-lifecycle.md):
  1. CivicActions is a supporting organization with a recommended attribution line.
  2. The 'civicactions' user is listed as a maintainer.
  3. The 'civicactions' maintainer has the Edit project, Administer maintainers, and Maintain issues permissions.

Usage:
  ./check_projects.py dkan_ai_query ai_revision_log
  ./check_projects.py https://www.drupal.org/project/dkan_ai_query

Exit code is 0 when every project passes all criteria, 1 otherwise, 2 on fetch errors.
"""
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

SITE = "https://www.drupal.org"
CIVICACTIONS_ORG_NID = "1121122"  # https://www.drupal.org/civicactions
MAINTAINER_USER = "civicactions"
RECOMMENDED_ATTRIBUTIONS = {
    "development and ideation",
    "provides time and technical support",
    "provided time for community contribution",
}
REQUIRED_PERMISSIONS = {
    "update project": "Edit project",
    "administer maintainers": "Administer maintainers",
    "maintain issues": "Maintain issues",
}
USER_AGENT = "civicactions-project-checker"


def machine_name(arg):
    return arg.rstrip("/").rsplit("/", 1)[-1]


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_attribution(name):
    """Return CivicActions' attribution line ('' if blank), or None if it is not a supporting organization."""
    query = urllib.parse.urlencode({"field_project_machine_name": name})
    projects = get_json(f"{SITE}/api-d7/node.json?{query}")["list"]
    if not projects:
        raise LookupError(f"project '{name}' not found")

    for ref in projects[0]["field_supporting_organizations"]:
        item = get_json(f"{SITE}/api-d7/field_collection_item/{ref['id']}.json")
        if item.get("archived") == "1" or item["field_supporting_organization"]["id"] != CIVICACTIONS_ORG_NID:
            continue
        return (item.get("field_how_they_helped") or "").strip()
    return None


def fetch_maintainers(name):
    """Return {username: {permission: bool}} for the project's maintainers."""
    data = get_json(f"{SITE}/project/{name}/maintainers.json")
    return {
        m["name"]: {perm: str(value) == "1" for perm, value in m["permissions"].items()}
        for m in data.values()
    }


def check(name):
    attribution = fetch_attribution(name)
    maintainers = fetch_maintainers(name)

    if attribution is None:
        attribution_note = "CivicActions not listed as a supporting organization"
    elif attribution.lower() in RECOMMENDED_ATTRIBUTIONS:
        attribution_note = f'"{attribution}"'
    else:
        attribution_note = f'"{attribution}" is not a recommended attribution line' if attribution else "attribution line is blank"

    perms = next((p for user, p in maintainers.items() if user.lower() == MAINTAINER_USER), None)
    missing = [label for key, label in REQUIRED_PERMISSIONS.items() if not (perms or {}).get(key)]

    return {
        "attribution_ok": attribution is not None and attribution.lower() in RECOMMENDED_ATTRIBUTIONS,
        "attribution_note": attribution_note,
        "maintainer_ok": perms is not None,
        "maintainers": list(maintainers),
        "permissions_ok": perms is not None and not missing,
        "permissions_note": "not a maintainer" if perms is None else f"missing: {', '.join(missing)}" if missing else "all present",
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
        except (urllib.error.URLError, LookupError, ValueError) as e:
            print(f"{name}: ERROR {e}", file=sys.stderr)
            errors = True
            continue
        ok = r["attribution_ok"] and r["maintainer_ok"] and r["permissions_ok"]
        all_pass &= ok
        print(f"{name}: {'PASS' if ok else 'FAIL'}")
        print(f"  attribution line: {'OK' if r['attribution_ok'] else 'FAIL'} - {r['attribution_note']}")
        print(f"  '{MAINTAINER_USER}' maintainer: {'OK' if r['maintainer_ok'] else 'FAIL'} "
              f"(maintainers: {', '.join(r['maintainers']) or 'none found'})")
        print(f"  '{MAINTAINER_USER}' permissions: {'OK' if r['permissions_ok'] else 'FAIL'} - {r['permissions_note']}")

    return 2 if errors else (0 if all_pass else 1)


if __name__ == "__main__":
    sys.exit(main())

# Drupal Project Maintenance Lifecycle

CivicActions' recommendations for creating, maintaining, handing off, and retiring Drupal.org projects: [drupal-project-maintenance-lifecycle.md](./drupal-project-maintenance-lifecycle.md).

## Project checker

[`check_projects.py`](./check_projects.py) checks Drupal.org projects against the recommendations. It uses only the Python standard library and needs no credentials.

```shell
./check_projects.py dkan_ai_query ai_revision_log
./check_projects.py https://www.drupal.org/project/dkan_ai_query
```

Example output:

```text
dkan_ai_query: PASS
  attribution line: OK - "provided time for community contribution"
  'civicactions' maintainer: OK (maintainers: civicactions, dcgoodwin)
  'civicactions' permissions: OK - all present
ai_revision_log: FAIL
  attribution line: FAIL - attribution line is blank
  'civicactions' maintainer: FAIL (maintainers: skyriter, talishkhan)
  'civicactions' permissions: FAIL - not a maintainer
```

Exit codes: `0` all projects pass, `1` at least one project fails, `2` at least one project could not be fetched.

### GitHub Actions

The [Check Drupal projects](./.github/workflows/check-projects.yml) workflow runs the checker on demand (it has no schedule). In the repository's Actions tab, choose **Check Drupal projects**, click **Run workflow**, and enter the project machine names separated by spaces or commas (e.g. `dkan_ai_query ai_revision_log`). The job fails if any project fails a criterion or cannot be fetched.

### Criteria

| Criterion | Passes when | Recommendation |
| --- | --- | --- |
| Attribution line | CivicActions is a supporting organization and its "how they helped" text is one of: `development and ideation`, `provides time and technical support`, `provided time for community contribution` (case-insensitive) | [How they helped](./drupal-project-maintenance-lifecycle.md#how-they-helped) |
| Maintainer | The `civicactions` user is listed in the project's Maintainers block | [Adding maintainers](./drupal-project-maintenance-lifecycle.md#adding-maintainers) |
| Maintainer permissions | The `civicactions` maintainer has Edit project, Administer maintainers, and Maintain issues | [Adding maintainers](./drupal-project-maintenance-lifecycle.md#adding-maintainers) |

### How it works and limitations

- Attribution comes from the Drupal.org API: `api-d7/node.json?field_project_machine_name=<name>` gives the project's `field_supporting_organizations`, and each `api-d7/field_collection_item/<id>.json` gives the organization and its "how they helped" text. CivicActions is matched by its organization node ID (`1121122`).
- Maintainers come from `https://www.drupal.org/project/<machine_name>/maintainers.json`.
- The checker makes one request per supporting organization, plus two per project.
- The maintainers endpoint is not a documented API, so it could change without notice.
- Maintainer permissions come from the same `maintainers.json` response (`update project`, `administer maintainers`, `maintain issues`). Extra permissions are fine.
- The recommendation only requires the `civicactions` maintainer for client or initiative projects. The script checks every project it is given, so only pass in projects where it applies.
- Client and partner organization attribution lines are not checked (the recommendation is to leave them blank unless the client says otherwise).

## TODO

- [ ] Add more criteria, for example:
    - Maintenance status matches the recommendation (Actively maintained vs. Minimally maintained)
    - Security advisory coverage is set
    - A client or partner supporting organization is listed
    - Retired projects follow the retirement steps (Unsupported, Obsolete, Not covered)
    - Project has a `README.md`, `CONTRIBUTING.md`, and `.gitlab-ci.yml`
- [ ] Add a scheduled run of the GitHub Actions workflow against a maintained list of projects (the workflow is on-demand only today).
- [ ] Read the list of projects to check from a file instead of command-line arguments (needed for the scheduled run).
- [ ] Add an option to limit the maintainer check to client and initiative projects.
- [ ] Add tests for the attribution and maintainer checks, using saved API responses as fixtures.

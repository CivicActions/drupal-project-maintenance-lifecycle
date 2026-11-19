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
  'civicactions' maintainer: OK (maintainers: dcgoodwin, civicactions)
ai_revision_log: FAIL
  attribution line: FAIL - attribution line is blank
  'civicactions' maintainer: FAIL (maintainers: talishkhan, skyriter)
```

Exit codes: `0` all projects pass, `1` at least one project fails, `2` at least one project could not be fetched.

### Criteria

| Criterion | Passes when | Recommendation |
| --- | --- | --- |
| Attribution line | CivicActions is a supporting organization and its "how they helped" text is one of: `development and ideation`, `provides time and technical support`, `provided time for community contribution` (case-insensitive) | [How they helped](./drupal-project-maintenance-lifecycle.md#how-they-helped) |
| Maintainer | The `civicactions` user is listed in the project's Maintainers block | [Adding maintainers](./drupal-project-maintenance-lifecycle.md#adding-maintainers) |

### How it works and limitations

- It reads the public project page (`https://www.drupal.org/project/<machine_name>`). The Drupal.org API does not expose maintainers, and GitLab's member API requires authentication.
- Drupal.org serves a JavaScript bot challenge to browser-like user agents, so the script sends a `curl/8` user agent to get the real page. If Drupal.org blocks that too, the script reports an error rather than a wrong result.
- It parses the page HTML, so a Drupal.org markup change could break it.
- The `civicactions` maintainer permissions (Edit project, Administer maintainers, Maintain issues) are not public and are not checked.
- The recommendation only requires the `civicactions` maintainer for client or initiative projects. The script checks every project it is given, so only pass in projects where it applies.
- Client and partner organization attribution lines are not checked (the recommendation is to leave them blank unless the client says otherwise).

## TODO

- [ ] Add more criteria, for example:
    - Maintenance status matches the recommendation (Actively maintained vs. Minimally maintained)
    - Security advisory coverage is set
    - A client or partner supporting organization is listed
    - Retired projects follow the retirement steps (Unsupported, Obsolete, Not covered)
    - Project has a `README.md`, `CONTRIBUTING.md`, and `.gitlab-ci.yml`
- [ ] Generate a GitHub Actions workflow that runs the checker, on a schedule and on demand, against a list of projects, and fails when any project does not pass.
- [ ] Read the list of projects to check from a file instead of command-line arguments (needed for the workflow).
- [ ] Add an option to limit the maintainer check to client and initiative projects.
- [ ] Check the `civicactions` maintainer permissions, if a reliable way to read them is found.
- [ ] Replace the page scraping and `curl/8` user agent workaround with Drupal.org API calls, including for maintainers. Attribution can already come from the API (`api-d7/node` and its `field_supporting_organizations` field collection items), but maintainers are not exposed there today, so find an API or authenticated endpoint that provides them.
- [ ] Add tests for the HTML parsing, using saved Drupal.org page fixtures.

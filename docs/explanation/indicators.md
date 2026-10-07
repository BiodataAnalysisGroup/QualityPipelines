# Indicators

An **indicator** is a measurable property of a software repository. resqui maps
each indicator to a plugin method that performs the check automatically.

## Built-in indicators

### `has_license` — HowFairIs

Looks for a file named `LICENSE` or `LICENSE.md` in the repository root using
the [howfairis](https://github.com/fair-software/howfairis) library. Requires a
GitHub token.

W3ID: `https://w3id.org/everse/i/indicators/software_has_license`

### `has_citation` — CFFConvert

Checks for a valid `CITATION.cff` file using
[cffconvert](https://github.com/citation-file-format/cffconvert). Both
presence and schema validity are verified.

W3ID: `https://w3id.org/everse/i/indicators/software_has_citation`

### `has_ci_tests` — OpenSSFScorecard

Checks whether the project has a functioning CI test setup, as determined by
the [OpenSSF Scorecard](https://github.com/ossf/scorecard). Runs via Docker.
Requires a GitHub token.

### `human_code_review_requirement` — OpenSSFScorecard

Checks whether pull requests require human review before merging, per the
OpenSSF Scorecard "Code-Review" check.

### `has_published_package` — OpenSSFScorecard

Checks whether the project publishes a package to a registry such as PyPI or
npm, per the OpenSSF Scorecard "Packaging" check.

### `has_no_security_leak` — Gitleaks

Scans the repository history for accidentally committed secrets (API keys,
tokens, passwords) using [Gitleaks](https://github.com/gitleaks/gitleaks).
Runs via Docker.

## Which revision is assessed

resqui assesses the commit it is run on (or the one given with `-b`). Most
plugins honour it, including RSFC. OpenSSF Scorecard is the exception: its
checks (`has_ci_tests`, `has_published_package`, ...) look at the repository
as a whole on GitHub, such as its pull-request history and the workflows on
the default branch. On a feature branch or pull request, their results reflect
the default branch rather than the changes under review.

## Interpreting results

Each indicator produces a `CheckResult` with:

| Field | Values |
|---|---|
| `outcome` | `pass` — indicator satisfied; `fail` — indicator not satisfied; `not_run` — the check could not be performed (e.g. its plugin failed to initialise, or the tool errored) |
| `output` | The raw result reported by the tool (plugin-specific, e.g. `valid`, `invalid`, `true`) |
| `status` | Schema.org action status IRI describing whether the check *action* completed |
| `evidence` | Human-readable finding from the underlying tool, or the reason a check did not run |

`outcome` is the field to rely on for pass/fail decisions (for example in CI,
see `--fail-on` in the [CLI reference](../reference/cli.md)). `status` only
says whether the check ran: most plugins report `schema:CompletedActionStatus`
whether or not the indicator is satisfied.

A failing or not-run check does **not** abort the run — all configured
indicators are always attempted, and not-run checks are recorded in the
report rather than left out.

## Status IDs

| Status IRI | Meaning |
|---|---|
| `schema:CompletedActionStatus` | The check ran (see `outcome` for the result) |
| `schema:FailedActionStatus` | The check could not be completed |

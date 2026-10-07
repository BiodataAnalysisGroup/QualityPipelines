"""Convert a resqui JSON assessment into a Markdown report.

Usable standalone:

    python -m resqui.markdown_report resqui_summary.json -o resqui_summary.md

or programmatically via `render` / `convert`.
"""

import argparse
import json
from pathlib import Path


def _escape(value):
    return str(value).replace("\\", "\\\\").replace("\n", " ").replace("|", "\\|").strip() or "-"


_LABELS = {"pass": "PASS", "fail": "FAIL", "not_run": "NOT RUN"}


def _outcome(check):
    """The check's outcome; reports written before `outcome` existed fall back to the status."""
    if "outcome" in check:
        return check["outcome"]
    return "pass" if check.get("status", {}).get("@id") == "schema:CompletedActionStatus" else "fail"


def render(data: dict) -> str:
    """Render a parsed resqui JSON assessment as a Markdown report."""
    assessed = data.get("assessedSoftware", {})
    checks = data.get("checks", [])
    outcomes = [_outcome(c) for c in checks]
    total = len(checks)
    passed = outcomes.count("pass")
    failed = outcomes.count("fail")
    not_run = outcomes.count("not_run")
    counts = f"{failed} failed, {not_run} not run" if not_run else f"{failed} failed"

    lines = [
        "# Software Quality Assessment",
        "",
        "## Run Information",
        "",
        f"- Date: {data.get('dateCreated', '-')}",
        f"- Project: {assessed.get('name', '-')}",
        f"- Repository: {assessed.get('url', '-')}",
        f"- Version: {assessed.get('softwareVersion', '-')}",
        f"- Checks: {passed}/{total} successful ({counts})",
        "",
        "## Assessments",
        "",
        "| Indicator | Tool | Tool Version | Output | Status | Evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for check, outcome in zip(checks, outcomes):
        status = _LABELS.get(outcome, outcome)
        indicator = check.get("assessesIndicator", {}).get("@id", "missing")
        tool = check.get("checkingSoftware", {}).get("name", "unknown")
        version = check.get("checkingSoftware", {}).get("version", "-")
        lines.append(
            "| "
            + " | ".join(
                _escape(value)
                for value in [indicator, tool, version, check.get("output", "-"), status, check.get("evidence", "-")]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def convert(input_path, output_path) -> None:
    """Read a resqui JSON file and write the Markdown report next to it."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Input and output paths must differ.")
    data = json.loads(input_path.read_text(encoding="utf-8"))
    output_path.write_text(render(data), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a resqui JSON summary into a Markdown report.")
    parser.add_argument("input", type=Path, help="Path to the resqui JSON summary file.")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Path to the Markdown report to write.")
    args = parser.parse_args()

    convert(args.input, args.output)
    print(f"Converted {args.input} -> {args.output}")


if __name__ == "__main__":
    main()

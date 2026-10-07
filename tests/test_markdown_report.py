import json
import tempfile
import unittest
from pathlib import Path

from resqui.markdown_report import render, convert


SAMPLE = {
    "dateCreated": "2026-01-01 00:00:00",
    "assessedSoftware": {
        "name": "myproject",
        "url": "https://github.com/user/myproject",
        "softwareVersion": "1.0.0",
    },
    "checks": [
        {
            "assessesIndicator": {"@id": "https://w3id.org/everse/i/indicators/license"},
            "checkingSoftware": {"name": "HowFairIs", "version": "0.14.2"},
            "status": {"@id": "schema:CompletedActionStatus"},
            "output": "valid",
            "evidence": "Found license file: 'LICENSE'.",
        },
        {
            "assessesIndicator": {"@id": "https://w3id.org/everse/i/indicators/citation"},
            "checkingSoftware": {"name": "CFFConvert", "version": "2.0.0"},
            "status": {"@id": "schema:FailedActionStatus"},
            "output": "invalid",
            "evidence": "No valid CITATION.cff | file found.",
        },
    ],
}


class TestRender(unittest.TestCase):
    def test_contains_title_and_run_information(self):
        markdown = render(SAMPLE)
        self.assertIn("# Software Quality Assessment", markdown)
        self.assertIn("- Project: myproject", markdown)
        self.assertIn("- Repository: https://github.com/user/myproject", markdown)

    def test_pass_fail_counts(self):
        markdown = render(SAMPLE)
        self.assertIn("- Checks: 1/2 successful (1 failed)", markdown)

    def test_status_column(self):
        markdown = render(SAMPLE)
        self.assertIn("| PASS |", markdown)
        self.assertIn("| FAIL |", markdown)

    def test_escapes_pipe_characters_in_evidence(self):
        markdown = render(SAMPLE)
        self.assertIn("No valid CITATION.cff \\| file found.", markdown)

    def test_escapes_backslash_before_pipe(self):
        from resqui.markdown_report import _escape

        self.assertEqual(_escape("a\\|b"), "a\\\\\\|b")

    def test_empty_checks(self):
        markdown = render({"assessedSoftware": {}, "checks": []})
        self.assertIn("- Checks: 0/0 successful (0 failed)", markdown)


    def test_outcome_field_takes_precedence_over_status(self):
        # A missing LICENSE is reported by the plugin as a completed action
        # that did not pass; the report must show it as FAIL.
        data = {
            "assessedSoftware": {},
            "checks": [
                {
                    "assessesIndicator": {"@id": "https://example.org/license"},
                    "status": {"@id": "schema:CompletedActionStatus"},
                    "output": "invalid",
                    "outcome": "fail",
                },
                {
                    "assessesIndicator": {"@id": "https://example.org/citation"},
                    "status": {"@id": "schema:CompletedActionStatus"},
                    "output": "valid",
                    "outcome": "pass",
                },
            ],
        }
        markdown = render(data)
        self.assertIn("- Checks: 1/2 successful (1 failed)", markdown)
        self.assertIn("| https://example.org/license | unknown | - | invalid | FAIL |", markdown)

    def test_not_run_checks_are_counted_and_labelled(self):
        data = {
            "assessedSoftware": {},
            "checks": [
                {
                    "assessesIndicator": {"@id": "https://example.org/ci"},
                    "status": {"@id": "schema:FailedActionStatus"},
                    "output": "missing",
                    "outcome": "not_run",
                    "evidence": "Docker is not available",
                },
                {
                    "assessesIndicator": {"@id": "https://example.org/license"},
                    "status": {"@id": "schema:CompletedActionStatus"},
                    "outcome": "pass",
                },
            ],
        }
        markdown = render(data)
        self.assertIn("- Checks: 1/2 successful (0 failed, 1 not run)", markdown)
        self.assertIn("| NOT RUN |", markdown)


class TestConvert(unittest.TestCase):
    def test_reads_json_and_writes_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "summary.json"
            output_path = Path(tmp) / "summary.md"
            input_path.write_text(json.dumps(SAMPLE))

            convert(input_path, output_path)

            content = output_path.read_text()
            self.assertIn("# Software Quality Assessment", content)
            self.assertIn("myproject", content)

    def test_rejects_identical_input_and_output_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(json.dumps(SAMPLE))

            with self.assertRaises(ValueError):
                convert(path, path)

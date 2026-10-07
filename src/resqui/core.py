#!/usr/bin/env python3
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import json

from resqui.api import APIClient


# Whether an indicator is satisfied ("pass"/"fail"), or could not be checked.
OUTCOMES = ("pass", "fail", "not_run")


@dataclass(frozen=True)
class Context:
    """A basic context to hold"""

    github_token: Optional[str] = None
    dashverse_token: Optional[str] = None
    dashverse_endpoint: Optional[str] = None


@dataclass
class CheckResult:
    """
    Datatype for indicator check results.
    """

    process: str = "Undefined process"
    status_id: str = "missing"
    output: str = "missing"
    evidence: str = "missing"
    success: bool = False

    def __bool__(self):
        return self.success


class Summary:
    """
    Summary of the software quality assessment.
    """

    def __init__(
        self,
        author,
        email,
        project_name,
        repo_url,
        software_version,
        branch_hash_or_tag,
    ):
        self.author = author
        self.email = email
        self.project_name = project_name
        self.repo_url = repo_url
        self.software_version = software_version
        self.branch_hash_or_tag = branch_hash_or_tag
        self.checks = []

    def add_indicator_result(self, indicator, checking_software, result):
        self._add_check(
            indicator,
            checking_software,
            result,
            outcome="pass" if result.success else "fail",
        )

    def add_not_run(self, indicator, checking_software, reason):
        """Record an indicator that could not be checked, e.g. its plugin failed to initialise."""
        result = CheckResult(
            process=f"{checking_software.name} could not check this indicator.",
            status_id="schema:FailedActionStatus",
            evidence=reason,
        )
        self._add_check(indicator, checking_software, result, outcome="not_run")

    def _add_check(self, indicator, checking_software, result, outcome):
        self.checks.append(
            {
                "@type": "CheckResult",
                "assessesIndicator": {"@id": indicator["@id"]},
                "checkingSoftware": {
                    "name": checking_software.name,
                    "version": checking_software.version,
                },
                "process": result.process,
                "status": {"@id": result.status_id},
                "output": result.output,
                "evidence": result.evidence,
                "outcome": outcome,
            }
        )

    def outcome_counts(self):
        counts = {outcome: 0 for outcome in OUTCOMES}
        for check in self.checks:
            counts[check["outcome"]] += 1
        return counts

    def to_json(self):
        return json.dumps(
            {
                "@context": "https://w3id.org/everse/rsqa/0.0.1/",
                "@type": "SoftwareQualityAssessment",
                "dateCreated": str(datetime.now()),
                "license": "CC0-1.0",
                "author": {"@type": "Person", "name": "Quality Pipeline"},
                "assessedSoftware": {
                    "@type": "SoftwareApplication",
                    "name": self.project_name,
                    "softwareVersion": self.software_version,
                    "url": self.repo_url,
                },
                "checks": self.checks,
            },
            sort_keys=True,
            indent=4,
        )

    def write(self, filename):
        with open(filename, "w") as f:
            f.write(self.to_json())

    def upload(self, dashverse_token=None, dashverse_endpoint=None):
        api = APIClient(dashverse_token, endpoint=dashverse_endpoint)
        api.post(self.to_json())

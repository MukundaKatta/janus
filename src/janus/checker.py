"""PR checker that validates pull requests against contribution guidelines.

Provides :class:`PRChecker` which runs a suite of checks on PR metadata
(branch name, commit messages, description, linked issue) and returns
structured :class:`CheckResult` objects.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CheckResult:
    """Outcome of a single validation check.

    Attributes:
        name: Short identifier for the check (e.g. ``"branch-naming"``).
        passed: Whether the check passed.
        message: Human-readable explanation.
    """

    name: str
    passed: bool
    message: str


# Recognised branch prefixes
_BRANCH_PREFIXES = (
    "feature/", "fix/", "docs/", "chore/", "refactor/",
    "test/", "ci/", "style/", "perf/", "build/",
)

# Conventional-commit pattern (simplified)
_COMMIT_RE = re.compile(
    r"^(feat|fix|docs|chore|refactor|test|ci|style|perf|build|revert)"
    r"(\(.+\))?!?:\s.+",
)

# Issue reference pattern (#123 or GH-123)
_ISSUE_REF_RE = re.compile(r"(#\d+|GH-\d+)", re.IGNORECASE)


class PRChecker:
    """Validate that a PR follows contribution guidelines.

    Instantiate with the PR metadata and call :meth:`run_all` to obtain a
    list of :class:`CheckResult` objects.
    """

    def __init__(
        self,
        branch_name: str = "",
        commit_messages: Optional[List[str]] = None,
        pr_description: str = "",
        pr_title: str = "",
    ) -> None:
        self.branch_name = branch_name
        self.commit_messages: List[str] = commit_messages or []
        self.pr_description = pr_description
        self.pr_title = pr_title

    # -- individual checks ---------------------------------------------------

    def check_branch_naming(self) -> CheckResult:
        """Branch must start with a recognised prefix (e.g. ``feature/``)."""
        if not self.branch_name:
            return CheckResult("branch-naming", False, "Branch name is empty.")
        for prefix in _BRANCH_PREFIXES:
            if self.branch_name.startswith(prefix):
                return CheckResult(
                    "branch-naming", True,
                    f"Branch '{self.branch_name}' uses prefix '{prefix}'.",
                )
        return CheckResult(
            "branch-naming", False,
            f"Branch '{self.branch_name}' does not start with a "
            f"recognised prefix ({', '.join(_BRANCH_PREFIXES)}).",
        )

    def check_commit_messages(self) -> CheckResult:
        """Every commit message must follow conventional-commit format."""
        if not self.commit_messages:
            return CheckResult(
                "commit-message", False, "No commit messages provided."
            )
        bad = [m for m in self.commit_messages if not _COMMIT_RE.match(m)]
        if bad:
            return CheckResult(
                "commit-message", False,
                f"{len(bad)} commit(s) do not follow conventional format: "
                + "; ".join(bad[:3]),
            )
        return CheckResult(
            "commit-message", True,
            "All commit messages follow conventional format.",
        )

    def check_description_present(self) -> CheckResult:
        """PR must include a non-trivial description."""
        text = self.pr_description.strip()
        if not text:
            return CheckResult(
                "description-present", False,
                "PR description is empty.",
            )
        if len(text) < 20:
            return CheckResult(
                "description-present", False,
                "PR description is too short (minimum 20 characters).",
            )
        return CheckResult(
            "description-present", True,
            "PR description is present and sufficient.",
        )

    def check_linked_issue(self) -> CheckResult:
        """PR description or title must reference an issue."""
        combined = f"{self.pr_title} {self.pr_description}"
        if _ISSUE_REF_RE.search(combined):
            return CheckResult(
                "linked-issue", True,
                "Issue reference found in PR.",
            )
        return CheckResult(
            "linked-issue", False,
            "No issue reference (#NNN or GH-NNN) found in title or description.",
        )

    # -- aggregate -----------------------------------------------------------

    def run_all(self) -> List[CheckResult]:
        """Run every check and return the results."""
        return [
            self.check_branch_naming(),
            self.check_commit_messages(),
            self.check_description_present(),
            self.check_linked_issue(),
        ]

    def all_passed(self) -> bool:
        """Return True only if every check passes."""
        return all(r.passed for r in self.run_all())

    def summary(self) -> str:
        """Return a human-readable summary of all check results."""
        results = self.run_all()
        lines = []
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"[{status}] {r.name}: {r.message}")
        passed = sum(1 for r in results if r.passed)
        lines.append(f"\n{passed}/{len(results)} checks passed.")
        return "\n".join(lines)

"""Tests for janus.checker — PR validation checks."""

from janus.checker import CheckResult, PRChecker


class TestCheckResult:
    def test_fields(self):
        r = CheckResult(name="test", passed=True, message="ok")
        assert r.name == "test"
        assert r.passed is True
        assert r.message == "ok"


class TestPRChecker:
    def test_branch_naming_pass(self):
        c = PRChecker(branch_name="feature/add-login")
        r = c.check_branch_naming()
        assert r.passed is True

    def test_branch_naming_fail(self):
        c = PRChecker(branch_name="my-branch")
        r = c.check_branch_naming()
        assert r.passed is False

    def test_branch_naming_empty(self):
        c = PRChecker(branch_name="")
        r = c.check_branch_naming()
        assert r.passed is False

    def test_commit_message_pass(self):
        c = PRChecker(commit_messages=["feat: add login page", "fix: typo in readme"])
        r = c.check_commit_messages()
        assert r.passed is True

    def test_commit_message_fail(self):
        c = PRChecker(commit_messages=["updated stuff", "feat: ok"])
        r = c.check_commit_messages()
        assert r.passed is False

    def test_commit_message_empty(self):
        c = PRChecker(commit_messages=[])
        r = c.check_commit_messages()
        assert r.passed is False

    def test_description_present_pass(self):
        c = PRChecker(pr_description="This PR adds the login feature with full test coverage.")
        r = c.check_description_present()
        assert r.passed is True

    def test_description_present_fail_empty(self):
        c = PRChecker(pr_description="")
        r = c.check_description_present()
        assert r.passed is False

    def test_description_present_fail_short(self):
        c = PRChecker(pr_description="short")
        r = c.check_description_present()
        assert r.passed is False

    def test_linked_issue_in_description(self):
        c = PRChecker(pr_description="Fixes #42 by updating the parser.")
        r = c.check_linked_issue()
        assert r.passed is True

    def test_linked_issue_in_title(self):
        c = PRChecker(pr_title="Fix login bug GH-99")
        r = c.check_linked_issue()
        assert r.passed is True

    def test_linked_issue_missing(self):
        c = PRChecker(pr_title="Fix login", pr_description="Updated the code")
        r = c.check_linked_issue()
        assert r.passed is False

    def test_run_all(self):
        c = PRChecker(
            branch_name="fix/login-crash",
            commit_messages=["fix: resolve login crash"],
            pr_description="This PR fixes the login crash reported in #10.",
            pr_title="Fix login crash #10",
        )
        results = c.run_all()
        assert len(results) == 4
        assert all(r.passed for r in results)

    def test_all_passed(self):
        c = PRChecker(
            branch_name="docs/update-readme",
            commit_messages=["docs: update readme"],
            pr_description="Updated the README with setup instructions for #5.",
            pr_title="Update README #5",
        )
        assert c.all_passed() is True

    def test_summary(self):
        c = PRChecker(branch_name="feature/x", commit_messages=["feat: x"],
                       pr_description="Adds feature x for issue #1.", pr_title="Feat x")
        summary = c.summary()
        assert "PASS" in summary
        assert "checks passed" in summary

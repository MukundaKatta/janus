"""Tests for janus.core — workflows, runner, and issue classifier."""

from janus.core import (
    ClassifiedIssue,
    ContributionGuide,
    IssueClassifier,
    Step,
    Workflow,
    WorkflowRunner,
)


# ---------------------------------------------------------------------------
# Step
# ---------------------------------------------------------------------------

class TestStep:
    def test_summary(self):
        s = Step(id="s1", title="Do thing", description="...",
                 commands=["git status"], tips=["be careful"])
        assert "[s1]" in s.summary()
        assert "1 command(s)" in s.summary()
        assert "1 tip(s)" in s.summary()

    def test_has_commands_true(self):
        s = Step(id="s1", title="T", description="D", commands=["echo hi"])
        assert s.has_commands() is True

    def test_has_commands_false(self):
        s = Step(id="s1", title="T", description="D")
        assert s.has_commands() is False


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

class TestWorkflow:
    def _make_wf(self):
        wf = Workflow(name="test-wf")
        wf.add_step(Step(id="a", title="A", description="step A"))
        wf.add_step(Step(id="b", title="B", description="step B"))
        return wf

    def test_add_and_count(self):
        wf = self._make_wf()
        assert wf.step_count() == 2

    def test_get_step_found(self):
        wf = self._make_wf()
        assert wf.get_step("a") is not None
        assert wf.get_step("a").title == "A"

    def test_get_step_missing(self):
        wf = self._make_wf()
        assert wf.get_step("z") is None

    def test_step_ids(self):
        wf = self._make_wf()
        assert wf.step_ids() == ["a", "b"]

    def test_remove_step(self):
        wf = self._make_wf()
        assert wf.remove_step("a") is True
        assert wf.step_count() == 1
        assert wf.remove_step("a") is False


# ---------------------------------------------------------------------------
# ContributionGuide
# ---------------------------------------------------------------------------

class TestContributionGuide:
    def test_add_and_list_workflows(self):
        guide = ContributionGuide()
        wf = Workflow(name="W1")
        guide.add_workflow(wf)
        assert "W1" in guide.list_workflows()

    def test_get_workflow(self):
        guide = ContributionGuide()
        wf = Workflow(name="W1")
        guide.add_workflow(wf)
        assert guide.get_workflow("W1") is wf
        assert guide.get_workflow("nope") is None

    def test_remove_workflow(self):
        guide = ContributionGuide()
        guide.add_workflow(Workflow(name="W1"))
        assert guide.remove_workflow("W1") is True
        assert guide.remove_workflow("W1") is False

    def test_materials(self):
        guide = ContributionGuide()
        guide.add_material("git", "Git basics guide")
        assert guide.get_material("git") == "Git basics guide"
        assert "git" in guide.list_materials()
        assert guide.get_material("nope") is None

    def test_build_standard_pr_workflow(self):
        wf = ContributionGuide.build_standard_pr_workflow()
        assert wf.name == "Standard PR Workflow"
        assert wf.step_count() >= 5
        ids = wf.step_ids()
        assert "fork" in ids
        assert "pr" in ids


# ---------------------------------------------------------------------------
# WorkflowRunner
# ---------------------------------------------------------------------------

class TestWorkflowRunner:
    def _runner(self):
        wf = ContributionGuide.build_standard_pr_workflow()
        return WorkflowRunner(wf)

    def test_execute_current(self):
        runner = self._runner()
        step = runner.execute_current()
        assert step is not None
        assert step.id == "fork"
        assert "fork" in runner.executed_steps

    def test_execute_all(self):
        runner = self._runner()
        executed = runner.execute_all()
        assert len(executed) == runner.workflow.step_count()
        assert runner.is_complete()

    def test_progress(self):
        runner = self._runner()
        assert runner.progress() == (0, runner.workflow.step_count())
        runner.execute_current()
        done, total = runner.progress()
        assert done == 1

    def test_reset(self):
        runner = self._runner()
        runner.execute_all()
        runner.reset()
        assert runner.is_complete() is False
        assert runner.executed_steps == []
        assert runner.command_log == []

    def test_command_log_populated(self):
        runner = self._runner()
        runner.execute_current()  # fork step has commands
        assert len(runner.command_log) > 0


# ---------------------------------------------------------------------------
# IssueClassifier
# ---------------------------------------------------------------------------

class TestIssueClassifier:
    def test_classify_good_first_issue(self):
        clf = IssueClassifier()
        result = clf.classify("Good first issue: fix typo", "This is easy")
        assert result.is_good_first_issue()

    def test_classify_bug(self):
        clf = IssueClassifier()
        result = clf.classify("App crash on login", "error when clicking")
        assert "bug" in result.categories

    def test_classify_feature(self):
        clf = IssueClassifier()
        result = clf.classify("Feature request: add dark mode", "")
        assert "feature" in result.categories

    def test_primary_category(self):
        clf = IssueClassifier()
        result = clf.classify("Bug: crash on startup", "error and fail")
        assert result.primary_category() is not None

    def test_classify_many(self):
        clf = IssueClassifier()
        issues = [
            ("Fix bug in parser", "crash"),
            ("Add new feature", "enhancement"),
        ]
        results = clf.classify_many(issues)
        assert len(results) == 2

    def test_find_good_first_issues(self):
        clf = IssueClassifier()
        issues = [
            ("Good first issue: update docs", "beginner friendly"),
            ("Complex refactor of internals", "advanced architecture"),
        ]
        good = clf.find_good_first_issues(issues)
        assert len(good) >= 1
        assert good[0].is_good_first_issue()

    def test_add_keywords(self):
        clf = IssueClassifier()
        clf.add_keywords("security", ["vulnerability", "cve", "exploit"])
        assert "security" in clf.list_categories()
        result = clf.classify("Security vulnerability found", "cve exploit")
        assert "security" in result.categories

    def test_empty_issue(self):
        clf = IssueClassifier()
        result = clf.classify("", "")
        assert result.primary_category() is None or result.confidence_scores.get(result.primary_category(), 0) == 0

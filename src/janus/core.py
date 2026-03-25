"""Core module for Janus contribution guide.

Provides workflow management, step-by-step PR guides, simulated git
operations, and issue classification by keyword analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Step:
    """A single step in a contribution workflow.

    Attributes:
        id: Unique identifier for the step (e.g. ``"fork-repo"``).
        title: Short human-readable title.
        description: Longer explanation of what the contributor should do.
        commands: Shell / git commands the contributor should run.
        tips: Helpful hints for beginners.
    """

    id: str
    title: str
    description: str
    commands: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Return a one-line summary of the step."""
        cmd_count = len(self.commands)
        tip_count = len(self.tips)
        return (
            f"[{self.id}] {self.title} "
            f"({cmd_count} command(s), {tip_count} tip(s))"
        )

    def has_commands(self) -> bool:
        """Return True if the step includes shell commands."""
        return len(self.commands) > 0


@dataclass
class Workflow:
    """An ordered sequence of steps that form a complete contribution workflow.

    Attributes:
        name: Name of the workflow (e.g. ``"Standard PR Workflow"``).
        steps: Ordered list of :class:`Step` objects.
    """

    name: str
    steps: List[Step] = field(default_factory=list)

    def add_step(self, step: Step) -> None:
        """Append a step to the workflow."""
        self.steps.append(step)

    def get_step(self, step_id: str) -> Optional[Step]:
        """Look up a step by its id.  Returns ``None`` if not found."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def step_ids(self) -> List[str]:
        """Return the ordered list of step ids."""
        return [s.id for s in self.steps]

    def step_count(self) -> int:
        """Return how many steps the workflow contains."""
        return len(self.steps)

    def remove_step(self, step_id: str) -> bool:
        """Remove a step by id.  Returns True if removed."""
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                self.steps.pop(i)
                return True
        return False


# ---------------------------------------------------------------------------
# ContributionGuide
# ---------------------------------------------------------------------------

class ContributionGuide:
    """Manages learning materials and contribution workflows.

    The guide holds a library of named workflows and provides helpers for
    building the standard PR workflow that most open-source projects follow.
    """

    def __init__(self) -> None:
        self._workflows: Dict[str, Workflow] = {}
        self._materials: Dict[str, str] = {}

    # -- workflow management -------------------------------------------------

    def add_workflow(self, workflow: Workflow) -> None:
        """Register a workflow by name."""
        self._workflows[workflow.name] = workflow

    def get_workflow(self, name: str) -> Optional[Workflow]:
        """Retrieve a workflow by name."""
        return self._workflows.get(name)

    def list_workflows(self) -> List[str]:
        """Return names of all registered workflows."""
        return list(self._workflows.keys())

    def remove_workflow(self, name: str) -> bool:
        """Remove a workflow.  Returns True if it existed."""
        if name in self._workflows:
            del self._workflows[name]
            return True
        return False

    # -- learning materials --------------------------------------------------

    def add_material(self, topic: str, content: str) -> None:
        """Store a learning material under *topic*."""
        self._materials[topic] = content

    def get_material(self, topic: str) -> Optional[str]:
        """Retrieve a learning material by topic."""
        return self._materials.get(topic)

    def list_materials(self) -> List[str]:
        """Return all material topics."""
        return list(self._materials.keys())

    # -- convenience builders ------------------------------------------------

    @staticmethod
    def build_standard_pr_workflow() -> Workflow:
        """Create the canonical pull-request workflow for beginners."""
        wf = Workflow(name="Standard PR Workflow")

        wf.add_step(Step(
            id="fork",
            title="Fork the repository",
            description="Create your own copy of the repository on GitHub.",
            commands=["# Click the 'Fork' button on the repo page"],
            tips=[
                "Forking creates a personal copy you can freely modify.",
                "You only need to fork once per project.",
            ],
        ))

        wf.add_step(Step(
            id="clone",
            title="Clone your fork",
            description="Download your fork to your local machine.",
            commands=[
                "git clone https://github.com/YOUR_USER/REPO.git",
                "cd REPO",
            ],
            tips=["Replace YOUR_USER and REPO with real values."],
        ))

        wf.add_step(Step(
            id="branch",
            title="Create a feature branch",
            description="Always work on a dedicated branch, not main.",
            commands=["git checkout -b feature/my-change"],
            tips=[
                "Use a descriptive branch name.",
                "Prefix with feature/, fix/, or docs/.",
            ],
        ))

        wf.add_step(Step(
            id="commit",
            title="Make and commit changes",
            description="Edit files, stage them, and commit with a message.",
            commands=[
                "git add .",
                'git commit -m "feat: describe your change"',
            ],
            tips=[
                "Write clear commit messages.",
                "Use conventional-commit prefixes (feat, fix, docs).",
            ],
        ))

        wf.add_step(Step(
            id="push",
            title="Push to your fork",
            description="Upload your branch to GitHub.",
            commands=["git push origin feature/my-change"],
            tips=["You may need to set upstream on first push."],
        ))

        wf.add_step(Step(
            id="pr",
            title="Open a Pull Request",
            description="Go to the original repo and open a PR from your branch.",
            commands=["# Click 'New Pull Request' on GitHub"],
            tips=[
                "Reference the issue you are fixing.",
                "Describe what you changed and why.",
            ],
        ))

        return wf


# ---------------------------------------------------------------------------
# WorkflowRunner — simulate git operations
# ---------------------------------------------------------------------------

class WorkflowRunner:
    """Simulates running through a workflow's git operations.

    Tracks which steps have been executed and maintains a log of simulated
    commands so that beginners can preview what will happen.
    """

    def __init__(self, workflow: Workflow) -> None:
        self._workflow = workflow
        self._executed: List[str] = []
        self._log: List[str] = []
        self._current_index: int = 0

    @property
    def workflow(self) -> Workflow:
        return self._workflow

    @property
    def executed_steps(self) -> List[str]:
        """Return ids of steps that have been executed."""
        return list(self._executed)

    @property
    def command_log(self) -> List[str]:
        """Return the full command log."""
        return list(self._log)

    def current_step(self) -> Optional[Step]:
        """Return the next step to execute, or None if done."""
        if self._current_index < len(self._workflow.steps):
            return self._workflow.steps[self._current_index]
        return None

    def execute_current(self) -> Optional[Step]:
        """Simulate executing the current step.

        Logs all commands and advances the pointer.  Returns the step that
        was executed, or ``None`` if the workflow is already complete.
        """
        step = self.current_step()
        if step is None:
            return None
        for cmd in step.commands:
            self._log.append(f"[{step.id}] $ {cmd}")
        self._executed.append(step.id)
        self._current_index += 1
        return step

    def execute_all(self) -> List[Step]:
        """Execute every remaining step and return them."""
        executed = []
        while True:
            step = self.execute_current()
            if step is None:
                break
            executed.append(step)
        return executed

    def is_complete(self) -> bool:
        """Return True when every step has been executed."""
        return self._current_index >= len(self._workflow.steps)

    def progress(self) -> Tuple[int, int]:
        """Return ``(completed, total)`` counts."""
        return (self._current_index, len(self._workflow.steps))

    def reset(self) -> None:
        """Reset the runner to the beginning."""
        self._executed.clear()
        self._log.clear()
        self._current_index = 0


# ---------------------------------------------------------------------------
# IssueClassifier — keyword-based issue categorisation
# ---------------------------------------------------------------------------

# Keyword banks used for classification
_GOOD_FIRST_KEYWORDS: List[str] = [
    "good first issue", "beginner", "easy", "starter", "newcomer",
    "first-timer", "low-hanging", "simple", "trivial", "introductory",
    "help wanted",
]

_BUG_KEYWORDS: List[str] = [
    "bug", "error", "crash", "fail", "broken", "fix", "defect",
    "regression", "unexpected", "incorrect", "wrong", "issue",
    "not working", "exception",
]

_FEATURE_KEYWORDS: List[str] = [
    "feature", "enhancement", "request", "add", "new", "improve",
    "proposal", "suggestion", "wishlist", "idea", "implement",
    "support",
]


@dataclass
class ClassifiedIssue:
    """Result of classifying a single issue."""

    title: str
    body: str
    categories: List[str] = field(default_factory=list)
    confidence_scores: Dict[str, float] = field(default_factory=dict)

    def primary_category(self) -> Optional[str]:
        """Return the highest-confidence category, or None."""
        if not self.confidence_scores:
            return None
        return max(self.confidence_scores, key=self.confidence_scores.get)

    def is_good_first_issue(self) -> bool:
        return "good-first-issue" in self.categories


class IssueClassifier:
    """Classify GitHub issues by keyword analysis.

    Scans the issue title and body for known keyword patterns and assigns
    one or more categories: ``good-first-issue``, ``bug``, ``feature``.
    """

    def __init__(self) -> None:
        self._keyword_map: Dict[str, List[str]] = {
            "good-first-issue": list(_GOOD_FIRST_KEYWORDS),
            "bug": list(_BUG_KEYWORDS),
            "feature": list(_FEATURE_KEYWORDS),
        }

    def add_keywords(self, category: str, keywords: List[str]) -> None:
        """Register additional keywords for a category."""
        if category not in self._keyword_map:
            self._keyword_map[category] = []
        self._keyword_map[category].extend(keywords)

    def list_categories(self) -> List[str]:
        """Return all known categories."""
        return list(self._keyword_map.keys())

    def _score_text(self, text: str, keywords: List[str]) -> float:
        """Return a 0-1 confidence score based on keyword hits."""
        if not keywords:
            return 0.0
        text_lower = text.lower()
        hits = sum(1 for kw in keywords if kw in text_lower)
        return min(hits / max(len(keywords) * 0.3, 1.0), 1.0)

    def classify(self, title: str, body: str = "") -> ClassifiedIssue:
        """Classify an issue and return a :class:`ClassifiedIssue`."""
        combined = f"{title} {body}"
        scores: Dict[str, float] = {}
        categories: List[str] = []

        for cat, keywords in self._keyword_map.items():
            score = self._score_text(combined, keywords)
            scores[cat] = round(score, 4)
            if score > 0.0:
                categories.append(cat)

        return ClassifiedIssue(
            title=title,
            body=body,
            categories=categories,
            confidence_scores=scores,
        )

    def classify_many(
        self, issues: List[Tuple[str, str]]
    ) -> List[ClassifiedIssue]:
        """Classify a batch of ``(title, body)`` pairs."""
        return [self.classify(t, b) for t, b in issues]

    def find_good_first_issues(
        self, issues: List[Tuple[str, str]]
    ) -> List[ClassifiedIssue]:
        """Return only the issues classified as good-first-issue."""
        return [
            ci for ci in self.classify_many(issues)
            if ci.is_good_first_issue()
        ]

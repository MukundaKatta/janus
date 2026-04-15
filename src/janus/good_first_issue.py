"""Scoring helpers for beginner-friendly issue discovery.

Janus helps newcomers find their first contribution. This module is the
ranker: given a list of GitHub issues with labels, age, comment counts,
and a repo's overall activity, it assigns a beginner-friendliness score
so the UI can sort them in the right order.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


# Labels that GitHub / CNCF projects use to flag newcomer-friendly work.
_FRIENDLY_LABELS = frozenset(
    l.lower() for l in (
        "good first issue", "good-first-issue", "good first bug",
        "beginner friendly", "beginner-friendly", "help wanted",
        "up-for-grabs", "first-timers-only", "up for grabs",
        "hacktoberfest", "starter", "easy",
    )
)

_HEAVY_LABELS = frozenset(
    l.lower() for l in (
        "breaking", "refactor", "epic", "rfc", "design",
        "major", "area/architecture",
    )
)


@dataclass(frozen=True)
class Issue:
    number: int
    title: str
    body: str
    labels: tuple[str, ...]
    created_at: str  # ISO8601
    updated_at: str
    comments: int
    assignee: str | None
    state: str  # "open" | "closed"


@dataclass(frozen=True)
class RepoContext:
    stars: int
    open_issues: int
    recent_commits_30d: int
    has_contributing_md: bool


@dataclass(frozen=True)
class Score:
    issue: Issue
    score: float
    reasons: tuple[str, ...]


def score_issue(issue: Issue, repo: RepoContext, *, now: datetime | None = None) -> Score:
    if issue.state != "open":
        return Score(issue=issue, score=0.0, reasons=("closed",))
    if issue.assignee:
        return Score(issue=issue, score=0.0, reasons=("already assigned",))

    reasons: list[str] = []
    score = 0.0

    labels_lower = {l.lower() for l in issue.labels}
    if labels_lower & _FRIENDLY_LABELS:
        score += 3.0
        reasons.append("labeled beginner-friendly")
    if labels_lower & _HEAVY_LABELS:
        score -= 1.5
        reasons.append("labeled as heavy/design work")

    # Age: not too fresh (maintainer hasn't triaged), not stale (likely abandoned).
    age_days = _age_days(issue.created_at, now)
    if 2 <= age_days <= 120:
        score += 1.0
        reasons.append("triaged, still active")
    elif age_days > 365:
        score -= 0.8
        reasons.append("very stale")

    # Conversation signal: some discussion is good, 30+ comments usually means contention.
    if 0 < issue.comments <= 5:
        score += 0.6
        reasons.append("light discussion")
    elif issue.comments > 30:
        score -= 1.0
        reasons.append("heavy discussion — probably contentious")

    # Body length: a real issue has some explanation.
    body_len = len((issue.body or "").strip())
    if body_len >= 120:
        score += 0.5
    elif body_len < 20:
        score -= 0.5
        reasons.append("near-empty body")

    # Repo shape: favour active-but-not-massive repos.
    if 50 <= repo.stars <= 20_000:
        score += 0.5
    if repo.recent_commits_30d >= 5:
        score += 0.5
        reasons.append("repo is active")
    if repo.has_contributing_md:
        score += 0.5
        reasons.append("has CONTRIBUTING.md")

    return Score(issue=issue, score=round(score, 2), reasons=tuple(reasons))


def rank(issues: Iterable[Issue], repo: RepoContext) -> list[Score]:
    return sorted(
        (score_issue(i, repo) for i in issues),
        key=lambda s: s.score,
        reverse=True,
    )


def _age_days(iso: str, now: datetime | None) -> int:
    try:
        ts = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return 0
    now = now or datetime.now(timezone.utc)
    return max(0, (now - ts).days)

"""Skill-based matching between contributors and open-source issues.

Provides dataclasses for contributor and project profiles and a
:class:`SkillMatcher` that computes compatibility scores so newcomers
can find the issues best suited to their abilities and interests.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ContributorProfile:
    """Profile describing a potential contributor.

    Attributes:
        name: Display name.
        skills: Technical skills the contributor possesses (e.g. ``"python"``).
        interests: Topics the contributor is interested in (e.g. ``"testing"``).
        experience_level: One of ``"beginner"``, ``"intermediate"``, ``"advanced"``.
    """

    name: str
    skills: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    experience_level: str = "beginner"

    def has_skill(self, skill: str) -> bool:
        """Case-insensitive check for a skill."""
        return skill.lower() in [s.lower() for s in self.skills]

    def add_skill(self, skill: str) -> None:
        if not self.has_skill(skill):
            self.skills.append(skill)

    def add_interest(self, interest: str) -> None:
        low = interest.lower()
        if low not in [i.lower() for i in self.interests]:
            self.interests.append(interest)


@dataclass
class ProjectProfile:
    """Describes a project or issue that needs contributors.

    Attributes:
        name: Project or issue title.
        required_skills: Skills needed to work on the project.
        topics: Topical tags (e.g. ``"documentation"``, ``"api"``).
        difficulty: One of ``"beginner"``, ``"intermediate"``, ``"advanced"``.
    """

    name: str
    required_skills: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    difficulty: str = "beginner"


@dataclass
class CompatibilityScore:
    """The result of matching a contributor to a project.

    Attributes:
        contributor_name: Name of the contributor.
        project_name: Name of the project / issue.
        skill_score: 0-1 score based on skill overlap.
        interest_score: 0-1 score based on interest/topic overlap.
        difficulty_score: 0-1 score based on experience vs difficulty.
        overall_score: Weighted combination of the three component scores.
    """

    contributor_name: str
    project_name: str
    skill_score: float = 0.0
    interest_score: float = 0.0
    difficulty_score: float = 0.0
    overall_score: float = 0.0


_DIFFICULTY_RANK: Dict[str, int] = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
}


class SkillMatcher:
    """Match contributors to projects/issues by skills and interests.

    Scores are computed across three dimensions:

    * **Skill overlap** -- how many required skills the contributor has.
    * **Interest overlap** -- how many project topics match the contributor's
      interests.
    * **Difficulty fit** -- how well the contributor's experience level
      matches the issue difficulty.

    Each dimension yields a 0-1 score and the final ``overall_score`` is a
    weighted average (default weights: skill 0.5, interest 0.3, difficulty 0.2).
    """

    def __init__(
        self,
        skill_weight: float = 0.5,
        interest_weight: float = 0.3,
        difficulty_weight: float = 0.2,
    ) -> None:
        self.skill_weight = skill_weight
        self.interest_weight = interest_weight
        self.difficulty_weight = difficulty_weight

    # -- scoring helpers -----------------------------------------------------

    @staticmethod
    def _set_overlap(a: List[str], b: List[str]) -> float:
        """Return the fraction of *b* items present in *a* (case-insensitive)."""
        if not b:
            return 1.0  # nothing required means perfect match
        a_low = {s.lower() for s in a}
        hits = sum(1 for item in b if item.lower() in a_low)
        return hits / len(b)

    @staticmethod
    def _difficulty_fit(experience: str, difficulty: str) -> float:
        """Score how well experience matches difficulty.

        Returns 1.0 for exact match, 0.75 if one level apart, 0.5 if two
        levels apart.
        """
        exp_rank = _DIFFICULTY_RANK.get(experience.lower(), 1)
        diff_rank = _DIFFICULTY_RANK.get(difficulty.lower(), 1)
        gap = abs(exp_rank - diff_rank)
        if gap == 0:
            return 1.0
        if gap == 1:
            return 0.75
        return 0.5

    # -- public API ----------------------------------------------------------

    def score(
        self,
        contributor: ContributorProfile,
        project: ProjectProfile,
    ) -> CompatibilityScore:
        """Compute a :class:`CompatibilityScore` for a contributor/project pair."""
        skill = self._set_overlap(contributor.skills, project.required_skills)
        interest = self._set_overlap(contributor.interests, project.topics)
        difficulty = self._difficulty_fit(
            contributor.experience_level, project.difficulty
        )

        overall = (
            self.skill_weight * skill
            + self.interest_weight * interest
            + self.difficulty_weight * difficulty
        )

        return CompatibilityScore(
            contributor_name=contributor.name,
            project_name=project.name,
            skill_score=round(skill, 4),
            interest_score=round(interest, 4),
            difficulty_score=round(difficulty, 4),
            overall_score=round(overall, 4),
        )

    def rank_projects(
        self,
        contributor: ContributorProfile,
        projects: List[ProjectProfile],
    ) -> List[CompatibilityScore]:
        """Return projects ranked by compatibility (best first)."""
        scores = [self.score(contributor, p) for p in projects]
        scores.sort(key=lambda s: s.overall_score, reverse=True)
        return scores

    def rank_contributors(
        self,
        project: ProjectProfile,
        contributors: List[ContributorProfile],
    ) -> List[CompatibilityScore]:
        """Return contributors ranked by compatibility (best first)."""
        scores = [self.score(c, project) for c in contributors]
        scores.sort(key=lambda s: s.overall_score, reverse=True)
        return scores

    def best_match(
        self,
        contributor: ContributorProfile,
        projects: List[ProjectProfile],
    ) -> Optional[CompatibilityScore]:
        """Return the single best project for a contributor, or None."""
        ranked = self.rank_projects(contributor, projects)
        return ranked[0] if ranked else None

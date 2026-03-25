"""Tests for janus.matcher — skill matching and compatibility scoring."""

from janus.matcher import (
    CompatibilityScore,
    ContributorProfile,
    ProjectProfile,
    SkillMatcher,
)


class TestContributorProfile:
    def test_has_skill(self):
        c = ContributorProfile(name="Alice", skills=["Python", "JavaScript"])
        assert c.has_skill("python") is True
        assert c.has_skill("rust") is False

    def test_add_skill_dedup(self):
        c = ContributorProfile(name="Bob", skills=["python"])
        c.add_skill("Python")  # duplicate (case-insensitive)
        assert len(c.skills) == 1
        c.add_skill("go")
        assert len(c.skills) == 2

    def test_add_interest(self):
        c = ContributorProfile(name="Carol")
        c.add_interest("testing")
        c.add_interest("Testing")  # duplicate
        assert len(c.interests) == 1


class TestSkillMatcher:
    def _matcher(self):
        return SkillMatcher()

    def test_perfect_match(self):
        m = self._matcher()
        c = ContributorProfile(
            name="Alice",
            skills=["python", "testing"],
            interests=["api"],
            experience_level="beginner",
        )
        p = ProjectProfile(
            name="Easy API fix",
            required_skills=["python"],
            topics=["api"],
            difficulty="beginner",
        )
        score = m.score(c, p)
        assert score.overall_score > 0.8
        assert score.skill_score == 1.0

    def test_no_overlap(self):
        m = self._matcher()
        c = ContributorProfile(name="Bob", skills=["java"], interests=["mobile"])
        p = ProjectProfile(
            name="Rust CLI",
            required_skills=["rust", "cli"],
            topics=["systems"],
            difficulty="advanced",
        )
        score = m.score(c, p)
        assert score.skill_score == 0.0
        assert score.overall_score < 0.5

    def test_rank_projects(self):
        m = self._matcher()
        c = ContributorProfile(name="Carol", skills=["python"], interests=["docs"])
        projects = [
            ProjectProfile(name="Rust thing", required_skills=["rust"]),
            ProjectProfile(name="Python docs", required_skills=["python"], topics=["docs"]),
        ]
        ranked = m.rank_projects(c, projects)
        assert ranked[0].project_name == "Python docs"

    def test_rank_contributors(self):
        m = self._matcher()
        p = ProjectProfile(name="Python API", required_skills=["python"], topics=["api"])
        contributors = [
            ContributorProfile(name="Expert", skills=["python", "api"], interests=["api"]),
            ContributorProfile(name="Newbie", skills=["html"]),
        ]
        ranked = m.rank_contributors(p, contributors)
        assert ranked[0].contributor_name == "Expert"

    def test_best_match(self):
        m = self._matcher()
        c = ContributorProfile(name="Dan", skills=["go"])
        projects = [
            ProjectProfile(name="Go tool", required_skills=["go"]),
            ProjectProfile(name="Java tool", required_skills=["java"]),
        ]
        best = m.best_match(c, projects)
        assert best is not None
        assert best.project_name == "Go tool"

    def test_best_match_empty(self):
        m = self._matcher()
        c = ContributorProfile(name="Eve")
        best = m.best_match(c, [])
        assert best is None

    def test_difficulty_scoring(self):
        m = self._matcher()
        c = ContributorProfile(name="Finn", skills=["python"], experience_level="advanced")
        p = ProjectProfile(name="Hard task", required_skills=["python"], difficulty="advanced")
        score = m.score(c, p)
        assert score.difficulty_score == 1.0

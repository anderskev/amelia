"""Tests for amelia.core.types."""

from amelia.core.types import Profile


class TestProfile:
    """Tests for Profile model."""

    def test_profile_validator_model_defaults_to_none(self) -> None:
        """Profile should have validator_model defaulting to None."""
        profile = Profile(
            name="test",
            driver="api:openrouter",
            model="gpt-4",
            tracker="github",
        )
        assert profile.validator_model is None

    def test_profile_validator_model_can_be_set(self) -> None:
        """Profile should accept validator_model as optional string."""
        profile = Profile(
            name="test",
            driver="api:openrouter",
            model="gpt-4",
            tracker="github",
            validator_model="gpt-4o-mini",
        )
        assert profile.validator_model == "gpt-4o-mini"


def test_profile_has_plan_path_pattern_with_default() -> None:
    from amelia.core.types import Profile

    profile = Profile(name="test", driver="cli:claude", model="sonnet")
    assert profile.plan_path_pattern == "docs/plans/{date}-{issue_key}.md"


def test_profile_plan_path_pattern_is_configurable() -> None:
    from amelia.core.types import Profile

    profile = Profile(
        name="test",
        driver="cli:claude",
        model="sonnet",
        plan_path_pattern=".amelia/{issue_key}-plan.md",
    )
    assert profile.plan_path_pattern == ".amelia/{issue_key}-plan.md"

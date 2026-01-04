"""Tests for amelia.core.types."""


def test_profile_has_plan_path_pattern_with_default():
    from amelia.core.types import Profile

    profile = Profile(name="test", driver="cli:claude", model="sonnet")
    assert profile.plan_path_pattern == "docs/plans/{date}-{issue_key}.md"


def test_profile_plan_path_pattern_is_configurable():
    from amelia.core.types import Profile

    profile = Profile(
        name="test",
        driver="cli:claude",
        model="sonnet",
        plan_path_pattern=".amelia/{issue_key}-plan.md",
    )
    assert profile.plan_path_pattern == ".amelia/{issue_key}-plan.md"

import pytest
from pydantic import ValidationError

from amelia.core.types import Profile


def test_work_profile_cli_constraint():
    """
    Ensure that a profile named 'work' cannot use API drivers.
    This is a business rule for enterprise compliance.
    """
    # Work profile with CLI driver should be valid
    work_profile_cli = Profile(name="work", driver="cli:claude", tracker="jira", strategy="single")
    assert work_profile_cli.driver == "cli:claude"

    # Work profile with API driver should raise
    with pytest.raises(ValidationError, match="work.*cannot use.*api"):
        Profile(name="work", driver="api:openai", tracker="jira", strategy="single")

    # Non-work profiles can use any driver
    home_profile = Profile(name="home", driver="api:openai", tracker="github", strategy="single")
    assert home_profile.driver == "api:openai"

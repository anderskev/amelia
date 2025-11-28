import pytest

from amelia.drivers.api.openai import ApiDriver


def test_api_driver_openai_only_scope():
    """
    Verifies that the ApiDriver, in its MVP form, is scoped to OpenAI only
    and raises an error for unsupported providers.
    """
    # Valid OpenAI models should work
    valid_driver = ApiDriver(model="openai:gpt-4o")
    assert valid_driver is not None

    # Also accept shorthand
    valid_driver2 = ApiDriver(model="openai:gpt-4o-mini")
    assert valid_driver2 is not None

    # Non-OpenAI providers should raise
    with pytest.raises(ValueError, match="Unsupported provider"):
        ApiDriver(model="anthropic:claude-3")

    with pytest.raises(ValueError, match="Unsupported provider"):
        ApiDriver(model="gemini:pro")

"""Tests for RetryConfig model."""

from amelia.core.types import RetryConfig


class TestRetryConfigDefaults:
    """Test default values for RetryConfig."""

    def test_default_values(self):
        """RetryConfig has sensible defaults."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0

"""Tests for server configuration."""
import os
from pathlib import Path
from unittest.mock import patch

from amelia.server.config import ServerConfig


class TestWorkingDir:
    """Tests for working_dir configuration."""

    def test_working_dir_defaults_to_none(self) -> None:
        """working_dir should be None by default."""
        config = ServerConfig()
        assert config.working_dir is None

    def test_working_dir_from_env_var(self) -> None:
        """working_dir should be set from AMELIA_WORKING_DIR env var."""
        with patch.dict(os.environ, {"AMELIA_WORKING_DIR": "/tmp/test-repo"}):
            config = ServerConfig()
            assert config.working_dir == Path("/tmp/test-repo")

    def test_working_dir_expands_user(self) -> None:
        """working_dir should expand ~ to home directory."""
        with patch.dict(os.environ, {"AMELIA_WORKING_DIR": "~/projects/repo"}):
            config = ServerConfig()
            assert config.working_dir == Path.home() / "projects" / "repo"

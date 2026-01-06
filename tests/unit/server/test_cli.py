"""Tests for server CLI commands."""
import os
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from amelia.main import app


class TestServerCLI:
    """Tests for 'amelia server' command."""

    @pytest.fixture
    def runner(self):
        """Typer CLI test runner."""
        return CliRunner()

    def test_server_command_exists(self, runner):
        """'amelia server' command is registered."""
        result = runner.invoke(app, ["server", "--help"])
        assert result.exit_code == 0
        assert "Amelia API server commands" in result.stdout

    @pytest.mark.parametrize("args,env,expected_port,expected_host", [
        ([], {}, 8420, "127.0.0.1"),
        (["--port", "9000"], {}, 9000, "127.0.0.1"),
        (["--bind-all"], {}, 8420, "0.0.0.0"),
        ([], {"AMELIA_PORT": "9999"}, 9999, "127.0.0.1"),
        (["--port", "8000"], {"AMELIA_PORT": "9999"}, 8000, "127.0.0.1"),  # CLI overrides env
    ])
    def test_server_config(
        self, runner: CliRunner, args: list[str], env: dict[str, str], expected_port: int, expected_host: str
    ) -> None:
        """Test server configuration from CLI args and environment."""
        with patch.dict(os.environ, env, clear=False):
            with patch("uvicorn.run") as mock_run:
                mock_run.side_effect = KeyboardInterrupt()
                runner.invoke(app, ["server"] + args)
                call_kwargs = mock_run.call_args.kwargs
                assert call_kwargs["port"] == expected_port
                assert call_kwargs["host"] == expected_host

    def test_server_bind_all_shows_warning(self, runner):
        """--bind-all shows security warning."""
        with patch("uvicorn.run") as mock_run:
            mock_run.side_effect = KeyboardInterrupt()
            result = runner.invoke(app, ["server", "--bind-all"])

            assert "Warning" in result.stdout or "warning" in result.stdout.lower()

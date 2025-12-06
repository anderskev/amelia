import subprocess
from unittest.mock import AsyncMock, patch

import yaml
from typer.testing import CliRunner

from amelia.agents.architect import TaskListResponse
from amelia.agents.reviewer import ReviewResponse
from amelia.core.state import Task
from amelia.main import app


runner = CliRunner()


def test_cli_review_local_output(settings_file_factory):
    """
    Verifies that 'amelia review --local' outputs review suggestions to stdout
    when executed in a 'Work' profile.
    """
    settings_data = {
        "active_profile": "work",
        "profiles": {
            "work": {"name": "work", "driver": "cli:claude", "tracker": "none", "strategy": "single"}
        }
    }
    settings_path = settings_file_factory(settings_data)

    with runner.isolated_filesystem(temp_dir=settings_path.parent):
        settings_file_factory(settings_data)

        # Setup git repo
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)

        # Create file and commit (use -c flags to ensure config is applied)
        with open("test.txt", "w") as f:
            f.write("initial content")
        subprocess.run(["git", "add", "test.txt"], check=True, capture_output=True)
        subprocess.run([
            "git", "-c", "user.email=test@example.com", "-c", "user.name=Test User",
            "commit", "-m", "initial"
        ], check=True, capture_output=True)

        # Make change (unstaged)
        with open("test.txt", "w") as f:
            f.write("changed content")

        # Write settings.amelia.yaml to CWD
        with open("settings.amelia.yaml", "w") as f:
            yaml.dump(settings_data, f)

        with patch("amelia.drivers.factory.DriverFactory.get_driver") as mock_get_driver:
            mock_driver = AsyncMock()
            mock_driver.generate.return_value = ReviewResponse(
                approved=False,
                comments=["Change is bad"],
                severity="medium"
            )
            mock_get_driver.return_value = mock_driver

            result = runner.invoke(app, ["review", "--local"])

            if result.exit_code != 0:
                print(result.stdout)
                print(result.stderr)

            assert result.exit_code == 0
            assert "Starting Amelia Review process" in result.stdout
            assert "Found local changes" in result.stdout
            assert "Reviewer completed review" in result.stdout or "REVIEW RESULT" in result.stdout
            assert "Change is bad" in result.stdout


def test_cli_plan_only_command(settings_file_factory):
    """
    Verifies that 'amelia plan-only' command generates and prints a plan.
    """
    settings_data = {
        "active_profile": "default",
        "profiles": {
            "default": {"name": "default", "driver": "cli:claude", "tracker": "noop", "strategy": "single"}
        }
    }
    settings_path = settings_file_factory(settings_data)

    with runner.isolated_filesystem(temp_dir=settings_path.parent):
        with open("settings.amelia.yaml", "w") as f:
            yaml.dump(settings_data, f)

        with patch('amelia.drivers.cli.claude.ClaudeCliDriver.generate') as mock_generate:
            mock_generate.side_effect = AsyncMock(return_value=TaskListResponse(tasks=[
                Task(id="T1", description="Mock task 1", dependencies=[]),
                Task(id="T2", description="Mock task 2", dependencies=["T1"])
            ]))

            result = runner.invoke(app, ["plan-only", "PROJ-123"])

            assert result.exit_code == 0
            assert "--- GENERATED PLAN ---" in result.stdout
            assert "- [T1] Mock task 1" in result.stdout
            assert "- [T2] Mock task 2 (Dependencies: T1)" in result.stdout

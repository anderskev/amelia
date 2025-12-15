# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tests for git utilities (snapshot and revert)."""

import os
import subprocess
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from amelia.tools.git_utils import (
    get_batch_changed_files,
    revert_to_git_snapshot,
    take_git_snapshot,
)


def _get_isolated_git_env() -> dict[str, str]:
    """Get environment variables for isolated git operations.

    This ensures git commands don't read or modify your global config.
    """
    # Start with minimal environment (PATH needed for git binary)
    git_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        # Git identity (required for commits)
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@test.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@test.com",
        # Disable global/system config - prevents reading your ~/.gitconfig
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_SYSTEM": "/dev/null",
        # Disable hooks completely
        "GIT_TEMPLATE_DIR": "",
    }
    return git_env


@pytest.fixture
def git_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a git repo with initial commit.

    Fully isolated from user's git configuration to prevent:
    - Reading ~/.gitconfig or system gitconfig
    - Triggering any git hooks
    - Using git templates
    """
    git_env = _get_isolated_git_env()

    # Initialize git repo with explicit branch name (no config dependency)
    subprocess.run(
        ["git", "init", "--initial-branch=main"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
        env=git_env,
    )

    # Create initial file and commit
    (tmp_path / "file.txt").write_text("initial content")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, env=git_env)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path,
        check=True,
        env=git_env,
        capture_output=True,
    )

    # Patch environment for async git commands in git_utils.py
    with patch.dict(os.environ, git_env, clear=True):
        yield tmp_path


async def test_take_git_snapshot_captures_head_and_dirty_files(git_repo: Path) -> None:
    """Test that snapshot captures HEAD commit and dirty files."""
    # Create some dirty files
    (git_repo / "dirty1.txt").write_text("modified")
    (git_repo / "dirty2.txt").write_text("new file")

    snapshot = await take_git_snapshot(repo_path=git_repo)

    # Should capture HEAD commit (40-char SHA)
    assert len(snapshot.head_commit) == 40
    assert snapshot.head_commit.isalnum()

    # Should capture dirty files (untracked and modified)
    # dirty_files is a tuple of filenames without status prefixes
    assert "dirty1.txt" in snapshot.dirty_files
    assert "dirty2.txt" in snapshot.dirty_files

    # No stash should be created (we just track)
    assert snapshot.stash_ref is None


async def test_take_git_snapshot_no_dirty_files(git_repo: Path) -> None:
    """Test snapshot works when repo is clean."""
    snapshot = await take_git_snapshot(repo_path=git_repo)

    # Should still capture HEAD
    assert len(snapshot.head_commit) == 40

    # No dirty files
    assert len(snapshot.dirty_files) == 0


async def test_revert_restores_batch_changed_files(git_repo: Path) -> None:
    """Test that revert restores files changed during the batch."""
    # Take snapshot
    snapshot = await take_git_snapshot(repo_path=git_repo)

    # Simulate batch changes
    (git_repo / "file.txt").write_text("batch modified")
    (git_repo / "new_batch_file.txt").write_text("created by batch")

    # Revert
    await revert_to_git_snapshot(snapshot, repo_path=git_repo)

    # file.txt should be restored to original content
    assert (git_repo / "file.txt").read_text() == "initial content"

    # Note: new_batch_file.txt may still exist as untracked file
    # (revert doesn't delete untracked files, only restores tracked ones)


async def test_revert_preserves_user_manual_changes(git_repo: Path) -> None:
    """Test that dirty files from before batch are NOT reverted."""
    # Create user's manual changes BEFORE taking snapshot
    (git_repo / "user_file.txt").write_text("user created this")

    # Take snapshot (should capture user_file.txt as dirty)
    snapshot = await take_git_snapshot(repo_path=git_repo)

    # Simulate batch changes
    (git_repo / "file.txt").write_text("batch modified")

    # User modifies their file further during batch
    (git_repo / "user_file.txt").write_text("user modified during batch")

    # Revert
    await revert_to_git_snapshot(snapshot, repo_path=git_repo)

    # Batch changes should be reverted
    assert (git_repo / "file.txt").read_text() == "initial content"

    # User's file should NOT be reverted (it was dirty before batch)
    # It should still exist with whatever state it's in
    assert (git_repo / "user_file.txt").exists()


async def test_get_batch_changed_files(git_repo: Path) -> None:
    """Test getting files changed since snapshot."""
    # Take snapshot
    snapshot = await take_git_snapshot(repo_path=git_repo)

    # Make some changes
    (git_repo / "file.txt").write_text("modified")
    (git_repo / "new_file.txt").write_text("new")

    # Get changed files
    changed = await get_batch_changed_files(snapshot, repo_path=git_repo)

    # Should include modified file
    assert "file.txt" in changed

    # Should include new file (if tracked)
    # Note: untracked files won't show in git diff, only in git status


async def test_revert_with_no_changes(git_repo: Path) -> None:
    """Test that revert handles case with no changes gracefully."""
    # Take snapshot
    snapshot = await take_git_snapshot(repo_path=git_repo)

    # Don't make any changes

    # Revert should work without error
    await revert_to_git_snapshot(snapshot, repo_path=git_repo)

    # File should still have original content
    assert (git_repo / "file.txt").read_text() == "initial content"


async def test_get_batch_changed_files_with_deleted_file(git_repo: Path) -> None:
    """Test that deleted files are included in changed files."""
    # Take snapshot
    snapshot = await take_git_snapshot(repo_path=git_repo)

    # Delete a tracked file
    (git_repo / "file.txt").unlink()

    # Get changed files
    changed = await get_batch_changed_files(snapshot, repo_path=git_repo)

    # Should include deleted file
    assert "file.txt" in changed


async def test_revert_handles_filenames_with_shell_metacharacters(git_repo: Path) -> None:
    """Test that filenames with shell metacharacters are properly escaped.

    This test verifies protection against shell injection attacks.
    Without proper escaping, a filename like "test; rm -rf /" could execute
    arbitrary commands.
    """
    git_env = _get_isolated_git_env()

    # Create a file with a dangerous filename that contains shell metacharacters
    # Using semicolon which would allow command chaining in unescaped context
    dangerous_name = "test; echo pwned > pwned.txt"
    dangerous_file = git_repo / dangerous_name
    dangerous_file.write_text("initial content")

    # Commit the file
    subprocess.run(
        ["git", "add", dangerous_name],
        cwd=git_repo,
        check=True,
        env=git_env,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add file with dangerous name"],
        cwd=git_repo,
        check=True,
        env=git_env,
        capture_output=True,
    )

    # Take snapshot
    snapshot = await take_git_snapshot(repo_path=git_repo)

    # Modify the file
    dangerous_file.write_text("modified content")

    # Revert - this should properly escape the filename and NOT execute "echo pwned"
    await revert_to_git_snapshot(snapshot, repo_path=git_repo)

    # The file should be restored to original content
    assert dangerous_file.read_text() == "initial content"

    # Most importantly: the injected command should NOT have executed
    # If shell injection occurred, "pwned.txt" would exist
    assert not (git_repo / "pwned.txt").exists(), (
        "Shell injection detected: command in filename was executed"
    )


async def test_get_batch_changed_files_handles_special_characters_in_filenames(
    git_repo: Path,
) -> None:
    """Test that filenames with special characters are properly handled in diff.

    This verifies that shell metacharacters in filenames don't cause
    command injection when checking for changed files.
    """
    git_env = _get_isolated_git_env()

    # Create files with various shell metacharacters
    special_names = [
        "file with spaces.txt",
        "file;semicolon.txt",
        "file&ampersand.txt",
        "file|pipe.txt",
        "file$(command).txt",
        "file`backtick`.txt",
    ]

    for name in special_names:
        file_path = git_repo / name
        file_path.write_text("content")
        subprocess.run(
            ["git", "add", name],
            cwd=git_repo,
            check=True,
            env=git_env,
            capture_output=True,
        )

    subprocess.run(
        ["git", "commit", "-m", "Add files with special names"],
        cwd=git_repo,
        check=True,
        env=git_env,
        capture_output=True,
    )

    # Take snapshot
    snapshot = await take_git_snapshot(repo_path=git_repo)

    # Modify one of the files
    (git_repo / special_names[0]).write_text("modified")

    # Get changed files - should not cause shell injection
    changed = await get_batch_changed_files(snapshot, repo_path=git_repo)

    # Should detect the changed file
    assert special_names[0] in changed


async def test_revert_handles_filenames_with_dollar_signs(git_repo: Path) -> None:
    """Test that filenames with dollar signs (command substitution) are escaped.

    Without proper escaping, $(...) or `...` in filenames could execute commands.
    """
    git_env = _get_isolated_git_env()

    # Create file with command substitution syntax in name
    dangerous_name = "file$(echo danger).txt"
    dangerous_file = git_repo / dangerous_name
    dangerous_file.write_text("original")

    subprocess.run(
        ["git", "add", dangerous_name],
        cwd=git_repo,
        check=True,
        env=git_env,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add file with dollar sign"],
        cwd=git_repo,
        check=True,
        env=git_env,
        capture_output=True,
    )

    # Take snapshot
    snapshot = await take_git_snapshot(repo_path=git_repo)

    # Modify the file
    dangerous_file.write_text("modified")

    # Revert should properly escape the filename
    await revert_to_git_snapshot(snapshot, repo_path=git_repo)

    # File should be restored
    assert dangerous_file.read_text() == "original"

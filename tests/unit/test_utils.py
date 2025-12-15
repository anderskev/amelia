# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""Tests for core utility functions."""

from amelia.core.utils import strip_ansi


def test_strip_ansi_removes_color_codes() -> None:
    """Test that common color codes are removed."""
    # Red color
    assert strip_ansi("\x1b[31mERROR\x1b[0m") == "ERROR"
    # Bold green
    assert strip_ansi("\x1b[1;32mSUCCESS\x1b[0m") == "SUCCESS"
    # Blue color
    assert strip_ansi("\x1b[34mINFO\x1b[0m") == "INFO"
    # Yellow color with bold
    assert strip_ansi("\x1b[1;33mWARNING\x1b[0m") == "WARNING"


def test_strip_ansi_removes_cursor_movement() -> None:
    """Test that cursor movement sequences are removed."""
    # Clear line and move to column 1
    assert strip_ansi("\x1b[2K\x1b[1G") == ""
    # Move cursor up
    assert strip_ansi("\x1b[A") == ""
    # Move cursor to position
    assert strip_ansi("\x1b[10;20H") == ""


def test_strip_ansi_preserves_plain_text() -> None:
    """Test that plain text passes through unchanged."""
    plain_text = "This is plain text with no ANSI codes"
    assert strip_ansi(plain_text) == plain_text

    # Text with special characters but no ANSI
    text_with_chars = "Test √ ✓ × ÷ symbols"
    assert strip_ansi(text_with_chars) == text_with_chars


def test_strip_ansi_handles_empty_string() -> None:
    """Test edge case of empty string."""
    assert strip_ansi("") == ""


def test_strip_ansi_handles_multiple_codes() -> None:
    """Test text with many ANSI codes interleaved."""
    # Mixed color codes in one string
    text = "\x1b[32m✓\x1b[0m All tests \x1b[1mpassed\x1b[0m successfully"
    assert strip_ansi(text) == "✓ All tests passed successfully"

    # Multiple lines with different formatting
    multiline = "\x1b[31mError:\x1b[0m Something went wrong\n\x1b[32mSuccess:\x1b[0m Fixed it"
    assert strip_ansi(multiline) == "Error: Something went wrong\nSuccess: Fixed it"


def test_strip_ansi_handles_terminal_title_codes() -> None:
    """Test that terminal title setting codes are removed."""
    # OSC (Operating System Command) sequences
    text_with_title = "\x1b]0;Terminal Title\x07Content"
    assert strip_ansi(text_with_title) == "Content"

    # Combined with color codes
    combined = "\x1b]2;Title\x07\x1b[32mGreen Text\x1b[0m"
    assert strip_ansi(combined) == "Green Text"


def test_strip_ansi_handles_complex_real_world_output() -> None:
    """Test with realistic command output containing ANSI codes."""
    # Git-like status output
    git_status = "\x1b[32m M\x1b[0m file.txt\n\x1b[31m D\x1b[0m old.txt\n\x1b[32m??\x1b[0m new.txt"
    assert strip_ansi(git_status) == " M file.txt\n D old.txt\n?? new.txt"

    # Progress indicator
    progress = "\x1b[2K\x1b[1G\x1b[32m[=====>   ]\x1b[0m 50%"
    assert strip_ansi(progress) == "[=====>   ] 50%"

"""Verify CLI client dependencies are available."""
import pytest


def test_httpx_importable():
    """httpx should be importable for REST client."""
    import httpx
    assert httpx.__version__


def test_rich_importable():
    """rich should be importable for CLI output."""
    import rich
    # Verify core rich components are available
    from rich.console import Console
    assert Console is not None

"""Logging configuration for the server.

This module re-exports loguru's logger for consistency.
The project uses loguru for all logging (see CLAUDE.md).
"""
from loguru import logger


__all__ = ["logger"]

"""
Command-line interface for the productivity assistant.

This module contains the main CLI entry point and user interaction logic.
"""

from .cli import app as cli_app
from src.agents.core import main, run_client

__all__ = ["main", "run_client", "cli_app"]
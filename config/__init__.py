"""
Configuration management for the productivity assistant.

This module contains configuration classes, settings, and prompts.
"""

from .settings import Settings
from .prompts import get_system_prompt

__all__ = ["Settings", "get_system_prompt"]


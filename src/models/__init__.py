"""
Data models and schemas for the productivity assistant.

This module contains Pydantic models for structured data handling,
including goal information, habit tracking, and response schemas.
"""

from .schemas import (
    GoalInfo,
    HabitInfo,
    MilestoneInfo,
    ProgressLogInfo,
)
from .responses import ProductivityResponse

__all__ = [
    "GoalInfo",
    "HabitInfo", 
    "MilestoneInfo",
    "ProgressLogInfo",
    "ProductivityResponse",
]


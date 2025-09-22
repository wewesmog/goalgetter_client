"""
Pydantic schemas for structured data handling.

This module contains the core data models for goals, habits, milestones, and progress logs.
"""

from typing import Optional, Literal
from pydantic import BaseModel


class GoalInfo(BaseModel):
    """Structured goal information."""
    goal_id: str
    title: str
    description: str
    status: Literal["in_progress", "completed", "cancelled"]
    start_date: str
    target_date: Optional[str] = None


class HabitInfo(BaseModel):
    """Structured habit information."""
    habit_id: str
    title: str
    description: str
    status: Literal["in_progress", "completed", "cancelled"]
    frequency_type: Literal["day", "week", "month", "year"]
    frequency_value: int


class MilestoneInfo(BaseModel):
    """Structured milestone information."""
    milestone_id: str
    goal_id: str
    description: str
    status: Literal["pending", "in_progress", "completed"]
    target_date: Optional[str] = None


class ProgressLogInfo(BaseModel):
    """Structured progress log information."""
    log_id: str
    content: str
    log_type: str
    related_goal_id: Optional[str] = None
    related_habit_id: Optional[str] = None
    created_at: str


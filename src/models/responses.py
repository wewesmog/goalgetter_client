"""
Response models for the productivity assistant.

This module contains the structured response models for API responses.
"""

from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field


class ProductivityResponse(BaseModel):
    """Structured response from productivity assistant."""
    action_type: Literal["goals", "habits", "milestones", "progress", "general"]
    summary: str
    data: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)


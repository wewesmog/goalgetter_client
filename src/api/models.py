"""
API request and response models for the FastAPI endpoints.

This module contains Pydantic models for API requests and responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    """Telegram user data model."""
    id: int = Field(..., description="Telegram user ID")
    first_name: str = Field(..., description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    username: Optional[str] = Field(None, description="User's username")
    language_code: Optional[str] = Field(None, description="User's language code")
    is_bot: bool = Field(False, description="Whether user is a bot")
    is_premium: Optional[bool] = Field(None, description="Whether user has Telegram Premium")

class ChatRequest(BaseModel):
    """Request model for chat endpoint (Telegram format)."""
    message: str = Field(..., description="User message to send to the assistant")
    user: TelegramUser = Field(..., description="Telegram user data")
    chat_id: Optional[int] = Field(None, description="Telegram chat ID")
    message_id: Optional[int] = Field(None, description="Telegram message ID")


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message from the assistant")
    action_type: str = Field(..., description="Type of action performed")
    summary: str = Field(..., description="Summary of the response")
    suggestions: List[str] = Field(default_factory=list, description="Actionable suggestions")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data from the response")
    error: Optional[str] = Field(None, description="Error message if request failed")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Current timestamp")


class MemoryStatusResponse(BaseModel):
    """Response model for memory status endpoint."""
    thread_id: str = Field(..., description="Thread ID checked")
    has_memory: bool = Field(..., description="Whether memory exists for this thread")
    message_count: int = Field(..., description="Number of messages in memory")
    checkpoint_count: int = Field(..., description="Number of checkpoints")
    last_activity: Optional[str] = Field(None, description="Last activity timestamp")


class TelegramUpdate(BaseModel):
    """Telegram webhook update model."""
    update_id: int = Field(..., description="Update ID")
    message: Optional[Dict[str, Any]] = Field(None, description="Message data")
    edited_message: Optional[Dict[str, Any]] = Field(None, description="Edited message data")
    channel_post: Optional[Dict[str, Any]] = Field(None, description="Channel post data")
    edited_channel_post: Optional[Dict[str, Any]] = Field(None, description="Edited channel post data")


class TelegramWebhookResponse(BaseModel):
    """Response model for Telegram webhook endpoint."""
    ok: bool = Field(..., description="Whether the webhook was processed successfully")
    error: Optional[str] = Field(None, description="Error message if processing failed")

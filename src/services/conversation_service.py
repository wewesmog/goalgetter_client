"""
Conversation context and summary management service.

This module handles building conversation context and summaries for the LLM.
"""

from typing import List, Any
from src.utils.message_utils import build_conversation_context


class ConversationService:
    """Service for managing conversation context and summaries."""
    
    def __init__(self):
        pass
    
    def build_conversation_summary(self, state: Any) -> str:
        """Build conversation summary with user context."""
        # For now, return a simple summary - you can enhance this later
        return "User is a perfectionist who gets easily distracted and asks the same questions multiple times. User is enthusiastic about productivity but tends to overcomplicate simple tasks."
    
    def build_conversation_context(self, messages: List[Any]) -> str:
        """Build conversation context from message history."""
        return build_conversation_context(messages)


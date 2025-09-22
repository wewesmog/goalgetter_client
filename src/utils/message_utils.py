"""
Message processing and conversation context utilities.

This module provides utilities for message trimming and conversation context building.
"""

from typing import List, Any
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from config.settings import settings


def trim_messages(messages: List[Any], total_messages: int) -> List[Any]:
    """Trim messages based on conversation length and settings."""
    if total_messages <= settings.max_messages_before_trimming:
        return messages
    
    # Determine max_tokens based on message count
    if total_messages > 100:
        max_tokens = settings.max_tokens_heavy_trimming
    elif total_messages > 50:
        max_tokens = settings.max_tokens_moderate_trimming
    else:
        max_tokens = settings.max_tokens_light_trimming
    
    # Trim messages
    trimmed_messages = trim_messages(
        messages,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=max_tokens,
        start_on="human",
        end_on=("human", "tool"),
    )
    
    return trimmed_messages


def build_conversation_context(messages: List[Any]) -> str:
    """Build conversation context from message history."""
    if len(messages) <= 1:
        return ""
    
    # Get last 5 messages for context (excluding the current user message)
    recent_messages = messages[-6:-1] if len(messages) > 6 else messages[:-1]
    
    context_parts = ["CONVERSATION HISTORY:"]
    for i, msg in enumerate(recent_messages, 1):
        if hasattr(msg, 'content'):
            content = msg.content
            role = getattr(msg, 'role', 'unknown')
        elif isinstance(msg, dict):
            content = msg.get('content', 'No content')
            role = msg.get('role', 'unknown')
        else:
            content = str(msg)
            role = 'unknown'
        
        # Truncate long content
        if len(content) > 200:
            content = content[:200] + "..."
        
        context_parts.append(f"{i}. {role}: {content}")
    
    return "\n".join(context_parts)


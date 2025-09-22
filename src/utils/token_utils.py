"""
Token counting and management utilities.

This module provides utilities for counting tokens and managing context windows.
"""

from langchain_core.messages.utils import count_tokens_approximately


def count_tokens_approximately(text: str) -> int:
    """Count tokens in text using LangChain's token counter."""
    return count_tokens_approximately(text)


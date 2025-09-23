"""
Remote MCP wrapper for PydanticAI integration.

This module wraps the HTTPMCPClient to work with PydanticAI's tool system.
"""

from typing import Any, Dict, List
from pydantic_ai import tool
from src.services.mcp_service import HTTPMCPClient


class RemoteMCPWrapper:
    """Wrapper to make remote MCP client work with PydanticAI tools."""
    
    def __init__(self, mcp_client: HTTPMCPClient):
        self.mcp_client = mcp_client
    
    @tool
    async def insert_goal_tool(self, title: str, description: str, user_id: str, target_date: str = None, priority: str = "medium") -> Dict[str, Any]:
        """Insert a new goal for the user."""
        return await self.mcp_client.call_tool("insert_goal_tool", 
                                             title=title, 
                                             description=description, 
                                             user_id=user_id, 
                                             target_date=target_date, 
                                             priority=priority)
    
    @tool
    async def get_goals_tool(self, user_id: str, status: str = None, limit: int = 10) -> Dict[str, Any]:
        """Get goals for the user."""
        return await self.mcp_client.call_tool("get_goals_tool", 
                                             user_id=user_id, 
                                             status=status, 
                                             limit=limit)
    
    @tool
    async def update_goal_tool(self, goal_id: int, user_id: str, **kwargs) -> Dict[str, Any]:
        """Update an existing goal."""
        return await self.mcp_client.call_tool("update_goal_tool", 
                                             goal_id=goal_id, 
                                             user_id=user_id, 
                                             **kwargs)
    
    @tool
    async def delete_goal_tool(self, goal_id: int, user_id: str) -> Dict[str, Any]:
        """Delete a goal."""
        return await self.mcp_client.call_tool("delete_goal_tool", 
                                             goal_id=goal_id, 
                                             user_id=user_id)
    
    @tool
    async def insert_habit_tool(self, name: str, description: str, user_id: str, frequency: str = "daily", reminder_time: str = None) -> Dict[str, Any]:
        """Insert a new habit for the user."""
        return await self.mcp_client.call_tool("insert_habit_tool", 
                                             name=name, 
                                             description=description, 
                                             user_id=user_id, 
                                             frequency=frequency, 
                                             reminder_time=reminder_time)
    
    @tool
    async def get_habits_tool(self, user_id: str, status: str = None, limit: int = 10) -> Dict[str, Any]:
        """Get habits for the user."""
        return await self.mcp_client.call_tool("get_habits_tool", 
                                             user_id=user_id, 
                                             status=status, 
                                             limit=limit)
    
    @tool
    async def insert_milestone_tool(self, goal_id: int, title: str, description: str, user_id: str, target_date: str = None) -> Dict[str, Any]:
        """Insert a milestone for a goal."""
        return await self.mcp_client.call_tool("insert_milestone_tool", 
                                             goal_id=goal_id, 
                                             title=title, 
                                             description=description, 
                                             user_id=user_id, 
                                             target_date=target_date)
    
    @tool
    async def get_milestones_tool(self, goal_id: int, user_id: str, status: str = None) -> Dict[str, Any]:
        """Get milestones for a goal."""
        return await self.mcp_client.call_tool("get_milestones_tool", 
                                             goal_id=goal_id, 
                                             user_id=user_id, 
                                             status=status)
    
    @tool
    async def insert_progress_log_tool(self, user_id: str, notes: str, goal_id: int = None, habit_id: int = None) -> Dict[str, Any]:
        """Log progress for goals or habits."""
        return await self.mcp_client.call_tool("insert_progress_log_tool", 
                                             user_id=user_id, 
                                             notes=notes, 
                                             goal_id=goal_id, 
                                             habit_id=habit_id)
    
    @tool
    async def get_progress_logs_tool(self, user_id: str, goal_id: int = None, habit_id: int = None, limit: int = 10) -> Dict[str, Any]:
        """Get progress logs for the user."""
        return await self.mcp_client.call_tool("get_progress_logs_tool", 
                                             user_id=user_id, 
                                             goal_id=goal_id, 
                                             habit_id=habit_id, 
                                             limit=limit)

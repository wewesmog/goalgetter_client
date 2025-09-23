"""
MCP (Model Context Protocol) service for external tool integration.

This module handles the setup and configuration of MCP servers.
"""

from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP
from config.settings import settings


def create_mcp_server():
    """Create MCP server for goalgetter with environment-based configuration."""
    
    # Check if we should use remote MCP server
    if settings.mcp_server_mode == "remote" and settings.mcp_server_url:
        print(f"🔗 Using remote MCP server: {settings.mcp_server_url}")
        # Use official PydanticAI HTTP MCP client
        return MCPServerStreamableHTTP(settings.mcp_server_url)
    else:
        # Use local MCP server (default)
        print(f"🏠 Using local MCP server: {settings.mcp_server_path}")
        # Use official PydanticAI stdio MCP client  
        return MCPServerStdio(
            'uv', 
            args=['run', 'main.py'], 
            cwd=settings.mcp_server_path,
            timeout=settings.mcp_server_timeout
        )


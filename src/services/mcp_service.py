"""
MCP (Model Context Protocol) service for external tool integration.

This module handles the setup and configuration of MCP servers.
"""

import aiohttp
import asyncio
from typing import Dict, Any, List
from pydantic_ai.mcp import MCPServerStdio
from config.settings import settings


class HTTPMCPClient:
    """HTTP-based MCP client for remote servers."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool on the remote MCP server."""
        if not self.session:
            raise RuntimeError("HTTPMCPClient not properly initialized. Use 'async with' context.")
        
        url = f"{self.base_url}/{tool_name}"
        
        try:
            async with self.session.post(url, json=kwargs) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('result', result)
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        except Exception as e:
            raise Exception(f"Failed to call tool {tool_name}: {str(e)}")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the remote MCP server."""
        if not self.session:
            raise RuntimeError("HTTPMCPClient not properly initialized. Use 'async with' context.")
        
        url = f"{self.base_url.replace('/tools', '')}/tools"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('tools', [])
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        except Exception as e:
            raise Exception(f"Failed to list tools: {str(e)}")


def create_mcp_server():
    """Create MCP server for goalgetter with environment-based configuration."""
    
    # Check if we should use remote MCP server
    if settings.mcp_server_mode == "remote" and settings.mcp_server_url:
        print(f"🔗 Using remote MCP server: {settings.mcp_server_url}")
        return HTTPMCPClient(settings.mcp_server_url, settings.mcp_server_timeout)
    else:
        # Use local MCP server (default)
        print(f"🏠 Using local MCP server: {settings.mcp_server_path}")
        return MCPServerStdio(
            'uv', 
            args=['run', 'main.py'], 
            cwd=settings.mcp_server_path,
            timeout=settings.mcp_server_timeout
        )


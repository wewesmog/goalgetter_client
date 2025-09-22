"""
CLI interface for testing the productivity assistant.

This module provides a simple command-line interface for testing and development.
"""

import asyncio
import sys
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.agents.core import ProductivityAgent, LangGraphOrchestrator, run_main_loop
from src.services.memory_service import MemoryService
from src.utils.logging import setup_logfire
from config.settings import settings
import logfire

app = typer.Typer(help="Goalgetter Client CLI")
console = Console()


@app.command()
def test(
    message: str = typer.Argument(..., help="Message to send to the assistant"),
    user_id: str = typer.Option("123", help="User ID for the request"),
    thread_id: str = typer.Option("123", help="Thread ID for conversation"),
    use_memory: bool = typer.Option(False, help="Use in-memory storage instead of PostgreSQL")
):
    """Test a single message with the productivity assistant."""
    
    async def run_test():
        # Initialize Logfire
        setup_logfire()
        logfire.info("Starting CLI test", message=message, user_id=user_id, thread_id=thread_id)
        
        try:
            # Create productivity agent
            console.print("🔧 Creating productivity agent...", style="blue")
            productivity_agent = ProductivityAgent()
            
            # Setup memory service
            memory_service = MemoryService()
            
            if use_memory:
                # Use in-memory storage
                console.print("💾 Using in-memory storage", style="yellow")
                memory_checkpointer = memory_service.setup_memory_checkpointer()
                
                orchestrator = LangGraphOrchestrator(productivity_agent)
                await orchestrator.setup_with_checkpointer(memory_checkpointer)
                
                # Process the message
                async with productivity_agent.agent:
                    result = await orchestrator.process(message, thread_id)
                    
                    # Display result
                    if isinstance(result, dict) and "messages" in result:
                        last_message = result["messages"][-1]
                        content = last_message.get("content", str(last_message)) if isinstance(last_message, dict) else str(last_message)
                        
                        console.print(Panel(
                            Text(content, style="green"),
                            title="🤖 Assistant Response",
                            border_style="green"
                        ))
                    else:
                        console.print(f"Response: {result}")
                        
            else:
                # Use PostgreSQL
                console.print("💾 Using PostgreSQL storage", style="blue")
                async with memory_service.setup_postgres_checkpointer() as checkpointer:
                    orchestrator = LangGraphOrchestrator(productivity_agent)
                    await orchestrator.setup_with_checkpointer(checkpointer)
                    
                    # Process the message
                    async with productivity_agent.agent:
                        result = await orchestrator.process(message, thread_id)
                        
                        # Display result
                        if isinstance(result, dict) and "messages" in result:
                            last_message = result["messages"][-1]
                            content = last_message.get("content", str(last_message)) if isinstance(last_message, dict) else str(last_message)
                            
                            console.print(Panel(
                                Text(content, style="green"),
                                title="🤖 Assistant Response",
                                border_style="green"
                            ))
                        else:
                            console.print(f"Response: {result}")
            
            console.print("✅ Test completed successfully!", style="green")
            
        except Exception as e:
            console.print(f"❌ Test failed: {str(e)}", style="red")
            logfire.error("CLI test failed", error=str(e))
            sys.exit(1)
    
    asyncio.run(run_test())


@app.command()
def interactive(
    user_id: str = typer.Option("123", help="User ID for the conversation"),
    thread_id: str = typer.Option("123", help="Thread ID for conversation"),
    use_memory: bool = typer.Option(False, help="Use in-memory storage instead of PostgreSQL")
):
    """Start an interactive session with the productivity assistant."""
    
    async def run_interactive():
        # Initialize Logfire
        setup_logfire()
        logfire.info("Starting interactive CLI session", user_id=user_id, thread_id=thread_id)
        
        try:
            # Create productivity agent
            console.print("🔧 Creating productivity agent...", style="blue")
            productivity_agent = ProductivityAgent()
            
            # Setup memory service
            memory_service = MemoryService()
            
            if use_memory:
                # Use in-memory storage
                console.print("💾 Using in-memory storage", style="yellow")
                memory_checkpointer = memory_service.setup_memory_checkpointer()
                
                orchestrator = LangGraphOrchestrator(productivity_agent)
                await orchestrator.setup_with_checkpointer(memory_checkpointer)
                
                # Run interactive loop
                await run_main_loop(orchestrator, productivity_agent, thread_id, use_memory=True)
                
            else:
                # Use PostgreSQL
                console.print("💾 Using PostgreSQL storage", style="blue")
                async with memory_service.setup_postgres_checkpointer() as checkpointer:
                    orchestrator = LangGraphOrchestrator(productivity_agent)
                    await orchestrator.setup_with_checkpointer(checkpointer)
                    
                    # Run interactive loop
                    await run_main_loop(orchestrator, productivity_agent, thread_id, use_memory=False)
            
        except Exception as e:
            console.print(f"❌ Interactive session failed: {str(e)}", style="red")
            logfire.error("Interactive CLI session failed", error=str(e))
            sys.exit(1)
    
    asyncio.run(run_interactive())


@app.command()
def check_memory(
    thread_id: str = typer.Option("123", help="Thread ID to check")
):
    """Check the status of LangGraph memory."""
    
    async def run_check():
        # Initialize Logfire
        setup_logfire()
        logfire.info("Checking memory status", thread_id=thread_id)
        
        try:
            memory_service = MemoryService()
            
            async with memory_service.setup_postgres_checkpointer() as checkpointer:
                await memory_service.check_memory_status(checkpointer, thread_id)
                
        except Exception as e:
            console.print(f"❌ Memory check failed: {str(e)}", style="red")
            logfire.error("Memory check failed", error=str(e))
            sys.exit(1)
    
    asyncio.run(run_check())


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development")
):
    """Start the FastAPI server for external access."""
    import uvicorn
    
    console.print(f"🚀 Starting FastAPI server on {host}:{port}", style="blue")
    console.print("📚 API documentation available at http://localhost:8000/docs", style="green")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    app()

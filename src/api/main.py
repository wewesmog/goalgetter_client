"""
FastAPI main application for external access to the productivity assistant.

This module provides REST API endpoints for external applications to interact
with the productivity assistant using uvicorn.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.models import ChatRequest, ChatResponse, HealthResponse, MemoryStatusResponse, TelegramUpdate, TelegramWebhookResponse, TelegramUser
from src.agents.core import ProductivityAgent, LangGraphOrchestrator
from src.services.memory_service import MemoryService
from src.services.user_service import UserService
from src.utils.logging import setup_logfire
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import logfire

# Global variables for shared resources
productivity_agent: ProductivityAgent = None
orchestrator: LangGraphOrchestrator = None
memory_service: MemoryService = None
user_service: UserService = None
checkpointer = None
checkpointer_context = None


async def send_telegram_message(chat_id: int, text: str) -> Dict[str, Any]:
    """Send a message back to Telegram."""
    import os
    import aiohttp
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }) as response:
                result = await response.json()
                logfire.info("Telegram message sent", 
                           chat_id=chat_id, 
                           response_ok=result.get("ok", False),
                           message_length=len(text))
                return result
    except Exception as e:
        logfire.error("Failed to send Telegram message", error=str(e), chat_id=chat_id)
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global productivity_agent, orchestrator, memory_service, user_service, checkpointer, checkpointer_context
    
    # Startup
    logfire.info("Starting FastAPI application")
    
    try:
        # Initialize Logfire
        setup_logfire()
        
        # Create productivity agent
        logfire.info("Creating productivity agent for API")
        productivity_agent = ProductivityAgent()
        
        # Setup services
        memory_service = MemoryService()
        user_service = UserService()
        
        # Setup orchestrator with PostgreSQL (same as mcp_client_pydantic.py)
        try:
            # Import settings here to avoid circular imports
            from config.settings import settings
            # Debug: Print the actual database URL being used
            print(f"🔍 DEBUG: Using database URL: {settings.database_url}")
            
            # Create PostgreSQL checkpointer with connection pooling
            # Use a connection string that includes pooling parameters
            pool_url = settings.database_url
            if "?" in pool_url:
                pool_url += "&pool_min_conn=1&pool_max_conn=10&pool_timeout=30"
            else:
                pool_url += "?pool_min_conn=1&pool_max_conn=10&pool_timeout=30"
            
            checkpointer_context = AsyncPostgresSaver.from_conn_string(pool_url)
            checkpointer = await checkpointer_context.__aenter__()
            print("✅ PostgreSQL connection established with pooling")
            
            # Create orchestrator with checkpointer
            orchestrator = LangGraphOrchestrator(productivity_agent)
            await orchestrator.setup_with_checkpointer(checkpointer)
            
            logfire.info("FastAPI application startup complete with PostgreSQL")
            
            yield
                
        except Exception as e:
            logfire.warning("PostgreSQL failed, falling back to memory", error=str(e))
            print(f"⚠️ PostgreSQL connection failed: {str(e)}")
            print("🔄 Falling back to in-memory storage...")
            
            # Fallback to memory-only mode
            memory_checkpointer = memory_service.setup_memory_checkpointer()
            orchestrator = LangGraphOrchestrator(productivity_agent)
            await orchestrator.setup_with_checkpointer(memory_checkpointer)
            
            logfire.info("FastAPI application startup complete with memory fallback")
            print("✅ Using in-memory storage (no persistence)")
            
            yield
            
    except Exception as e:
        logfire.error("FastAPI startup failed", error=str(e))
        raise
    
    # Shutdown
    logfire.info("Shutting down FastAPI application")
    
    # Clean up checkpointer if it exists
    if checkpointer:
        try:
            await checkpointer_context.__aexit__(None, None, None)
            print("✅ PostgreSQL checkpointer closed")
        except Exception as e:
            print(f"⚠️ Error closing checkpointer: {e}")


# Create FastAPI app
app = FastAPI(
    title="Goalgetter Productivity Assistant API",
    description="REST API for the PydanticAI + MCP + LangGraph productivity assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    # Import settings here to avoid circular imports
    from config.settings import settings
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.service_version,
        timestamp=datetime.now().isoformat()
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint for interacting with the productivity assistant (Telegram format)."""
    try:
        # Extract Telegram user data
        user_id = str(request.user.id)  # Convert to string for consistency
        thread_id = user_id  # Use Telegram user ID as thread ID
        
        # Print to console for visibility
        print(f"\n🚀 **Telegram Chat Request**")
        print(f"👤 User ID: {user_id}")
        print(f"👤 Name: {request.user.first_name} {request.user.last_name or ''}")
        print(f"👤 Username: @{request.user.username or 'N/A'}")
        print(f"🌍 Language: {request.user.language_code or 'N/A'}")
        print(f"🧵 Thread ID: {thread_id}")
        print(f"💬 Chat ID: {request.chat_id}")
        print(f"📝 Message: {request.message}")
        
        # Log to Logfire
        logfire.info("Telegram chat request", 
                    message=request.message, 
                    user_id=user_id,
                    user_name=request.user.first_name,
                    username=request.user.username,
                    language_code=request.user.language_code,
                    chat_id=request.chat_id,
                    thread_id=thread_id)
        
        # Get or create user (non-blocking)
        telegram_user_data = {
            "id": request.user.id,
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "username": request.user.username,
            "language_code": request.user.language_code,
            "is_bot": request.user.is_bot,
            "is_premium": request.user.is_premium
        }
        
        # Start user management in background (don't wait)
        asyncio.create_task(user_service.get_or_create_user_async(telegram_user_data))
        
        # Process the request through the orchestrator immediately
        async with productivity_agent.agent:
            result = await orchestrator.process(request.message, thread_id, user_id)
            
            # Get message count from the result FIRST
            message_count = 0
            if isinstance(result, dict) and "messages" in result:
                message_count = len(result["messages"])
            
            # Print message count BEFORE processing response
            print(f"💬 **Messages in history: {message_count}**")
            
            # Extract response content - simplified
            if isinstance(result, dict) and "messages" in result:
                last_message = result["messages"][-1]
                if isinstance(last_message, dict):
                    content = last_message.get("content", str(last_message))
                else:
                    content = str(last_message)
            else:
                content = str(result)
            
            # Clean up the content formatting - extract actual response
            if "AgentRunResult" in content:
                # Extract the actual output from AgentRunResult
                import re
                match = re.search(r'output="([^"]*)"', content)
                if match:
                    content = match.group(1)
                    # Unescape quotes and newlines
                    content = content.replace('\\"', '"').replace('\\n', '\n')
            
            # Remove any remaining wrapper formatting
            content = content.replace("🎯 **Productivity Assistant Response**", "").strip()
            content = content.replace("Action: general", "").strip()
            content = content.replace("Summary:", "").strip()
            content = content.replace("---", "").strip()
            content = content.replace("*Powered by PydanticAI + MCP + LangGraph + Logfire*", "").strip()
            
            # Clean up extra whitespace and newlines
            content = content.strip()
            
            # Print final response stats
            print(f"📊 **API Response Stats**")
            print(f"👤 User ID: {user_id}")
            print(f"🧵 Thread ID: {thread_id}")
            print(f"📝 Response length: {len(content)} characters")
            
            # Log to Logfire
            logfire.info("API chat response generated", 
                        user_id=user_id,
                        thread_id=thread_id,
                        response_length=len(content), 
                        message_count=message_count)
            
            return ChatResponse(
                success=True,
                message=content,
                action_type="general",
                summary=content[:100] + "..." if len(content) > 100 else content,
                suggestions=[],
                next_steps=[],
                data={
                    "thread_id": thread_id, 
                    "user_id": user_id,
                    "user_name": request.user.first_name,
                    "username": request.user.username,
                    "language_code": request.user.language_code,
                    "chat_id": request.chat_id
                }
            )
            
    except Exception as e:
        logfire.error("API chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Chat request failed: {str(e)}")


@app.get("/memory/{user_id}", response_model=MemoryStatusResponse)
async def get_memory_status(user_id: str):
    """Get memory status for a specific user."""
    try:
        # Generate thread_id from user_id (same as chat endpoint)
        thread_id = f"user_{user_id}"
        
        logfire.info("API memory status request", user_id=user_id, thread_id=thread_id)
        
        # Get the latest checkpoint
        checkpoint = await orchestrator.checkpointer.aget_tuple({"configurable": {"thread_id": thread_id}})
        
        if checkpoint:
            # Extract message count
            messages = checkpoint.checkpoint.get('channel_values', {}).get('messages', [])
            message_count = len(messages)
            
            # Get checkpoint count
            all_checkpoints = []
            async for cp in orchestrator.checkpointer.alist({"configurable": {"thread_id": thread_id}}):
                all_checkpoints.append(cp)
            checkpoint_count = len(all_checkpoints)
            
            # Get last activity timestamp
            timestamp = checkpoint.checkpoint.get('ts', None)
            
            return MemoryStatusResponse(
                thread_id=thread_id,
                has_memory=True,
                message_count=message_count,
                checkpoint_count=checkpoint_count,
                last_activity=timestamp
            )
        else:
            return MemoryStatusResponse(
                thread_id=thread_id,
                has_memory=False,
                message_count=0,
                checkpoint_count=0,
                last_activity=None
            )
            
    except Exception as e:
        logfire.error("API memory status request failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Memory status request failed: {str(e)}")


@app.post("/telegram/telegram-webhook", response_model=TelegramWebhookResponse)
async def telegram_webhook(request: Request):
    """Telegram webhook endpoint that receives updates from Telegram."""
    try:
        # Get the raw JSON from Telegram
        update_data = await request.json()
        
        logfire.info("Telegram webhook received", update_id=update_data.get("update_id"))
        
        # Extract message data
        if "message" in update_data:
            message = update_data["message"]
            user_data = message["from"]
            chat_data = message["chat"]
            text = message.get("text", "")
            
            # Convert to your ChatRequest format
            chat_request = ChatRequest(
                message=text,
                user=TelegramUser(
                    id=user_data["id"],
                    first_name=user_data.get("first_name", ""),
                    last_name=user_data.get("last_name"),
                    username=user_data.get("username"),
                    language_code=user_data.get("language_code"),
                    is_bot=user_data.get("is_bot", False),
                    is_premium=user_data.get("is_premium", False)
                ),
                chat_id=chat_data["id"],
                message_id=message.get("message_id")
            )
            
            # Process through your existing chat endpoint
            response = await chat(chat_request)
            
            # Send response back to Telegram with error handling
            try:
                if response.success:
                    # For Telegram, send only the clean message content, not the full response structure
                    clean_message = response.message
                    
                    # Additional cleanup for Telegram users - remove any remaining technical formatting
                    clean_message = clean_message.replace("message:", "").strip()
                    clean_message = clean_message.replace("actiontype:", "").strip()  
                    clean_message = clean_message.replace("summary:", "").strip()
                    clean_message = clean_message.replace("data:", "").strip()
                    clean_message = clean_message.replace("suggestions:", "").strip()
                    clean_message = clean_message.replace("nextsteps:", "").strip()
                    clean_message = clean_message.replace("general", "").strip()
                    clean_message = clean_message.replace("None", "").strip()
                    
                    # Remove action labels and technical artifacts
                    clean_message = clean_message.replace("Action: goals", "").strip()
                    clean_message = clean_message.replace("Action: habits", "").strip() 
                    clean_message = clean_message.replace("Action:", "").strip()
                    clean_message = clean_message.replace("Data:", "").strip()
                    clean_message = clean_message.replace("Next Steps:", "").strip()
                    clean_message = clean_message.replace("goals", "", 1).strip()  # Remove first occurrence only
                    
                    # Fix escape characters - unescape quotes and newlines
                    clean_message = clean_message.replace("\\'", "'")  # Fix escaped apostrophes
                    clean_message = clean_message.replace('\\"', '"')  # Fix escaped quotes
                    clean_message = clean_message.replace("\\n", "\n")  # Fix escaped newlines
                    clean_message = clean_message.replace("\\\\", "\\")  # Fix double backslashes
                    
                    # Remove multiple newlines and clean up
                    import re
                    clean_message = re.sub(r'\n\s*\n', '\n\n', clean_message)  # Replace multiple newlines
                    clean_message = clean_message.strip()
                    
                    await send_telegram_message(chat_data["id"], clean_message)
                    logfire.info("Telegram webhook processed successfully", 
                               user_id=user_data["id"], 
                               chat_id=chat_data["id"])
                else:
                    # Send error message to user
                    error_msg = f"Sorry, I encountered an error: {response.error or 'Unknown error'}"
                    await send_telegram_message(chat_data["id"], error_msg)
                    logfire.error("Telegram webhook processing failed", 
                                user_id=user_data["id"], 
                                error=response.error)
            except Exception as telegram_error:
                # If sending to Telegram fails, log it but don't crash the webhook
                logfire.error("Failed to send message to Telegram", 
                            chat_id=chat_data["id"],
                            user_id=user_data["id"],
                            telegram_error=str(telegram_error))
                # Return success anyway so Telegram doesn't retry
                print(f"❌ Failed to send Telegram message: {telegram_error}")
            
            return TelegramWebhookResponse(ok=True)
        else:
            # Handle other update types (edited messages, channel posts, etc.)
            logfire.info("Telegram webhook received non-message update", 
                        update_type=list(update_data.keys()))
            return TelegramWebhookResponse(ok=True)
            
    except Exception as e:
        logfire.error("Telegram webhook error", error=str(e))
        return TelegramWebhookResponse(ok=False, error=str(e))


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Goalgetter Productivity Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "chat": "POST /chat",
            "memory": "GET /memory/{user_id}",
            "health": "GET /health"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logfire.error("Unhandled API exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

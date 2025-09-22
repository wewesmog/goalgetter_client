"""
PydanticAI + MCP + LangGraph + Logfire Integration
The ultimate productivity assistant with structured agents, external tools, orchestration, and tracing
"""

import os
import sys
import asyncio
import json
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime

# Core imports
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# PydanticAI imports
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.tools import Tool

# LangGraph imports
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.prebuilt import ToolNode

# MCP imports
from pydantic_ai.mcp import MCPServerStdio

# Logfire imports
import logfire

# Load environment variables
load_dotenv()

# Fix for Windows PostgreSQL async issue
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Initialize Logfire tracing
logfire.configure()  # Use default configuration
logfire.instrument_pydantic_ai()  # Enable PydanticAI instrumentation

# PydanticAI Models for structured responses
class GoalInfo(BaseModel):
    """Structured goal information"""
    goal_id: str
    title: str
    description: str
    status: Literal["in_progress", "completed", "cancelled"]
    start_date: str
    target_date: Optional[str] = None

class HabitInfo(BaseModel):
    """Structured habit information"""
    habit_id: str
    title: str
    description: str
    status: Literal["in_progress", "completed", "cancelled"]
    frequency_type: Literal["day", "week", "month", "year"]
    frequency_value: int

class MilestoneInfo(BaseModel):
    """Structured milestone information"""
    milestone_id: str
    goal_id: str
    description: str
    status: Literal["pending", "in_progress", "completed"]
    target_date: Optional[str] = None

class ProgressLogInfo(BaseModel):
    """Structured progress log information"""
    log_id: str
    content: str
    log_type: str
    related_goal_id: Optional[str] = None
    related_habit_id: Optional[str] = None
    created_at: str

class ProductivityResponse(BaseModel):
    """Structured response from productivity assistant"""
    action_type: Literal["goals", "habits", "milestones", "progress", "general"]
    summary: str
    data: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)

# MCP Server setup - using PydanticAI's native MCP integration
def create_mcp_server():
    """Create MCP server for goalgetter"""
    return MCPServerStdio(
        'uv', 
        args=['run', 'main.py'], 
        cwd='D:\\goalgetter',
        timeout=30
    )

class ProductivityAgent:
    """PydanticAI agent for productivity management"""
    
    def __init__(self):
        # Create MCP server
        self.mcp_server = create_mcp_server()
        
        # Create PydanticAI agent with MCP tools
        self.agent = Agent(
            model=OpenAIChatModel("gpt-4-0125-preview"),
            system_prompt=self._get_system_prompt(),
            toolsets=[self.mcp_server]
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the productivity agent"""
        return """You are a helpful personal productivity assistant who helps users manage their goals, habits, milestones, and progress logs.

ROLE AND PERSONALITY:
- You are encouraging, supportive, and productivity-focused
- You help users stay organized and motivated
- You provide actionable advice and suggestions
- You celebrate achievements and help overcome challenges

CONVERSATION CONTEXT:
- ALWAYS use the conversation history provided to understand context
- When user says "the latest one", "that goal", "my habit", etc., refer to the conversation history
- If conversation history shows recent goals/habits, use that context to understand what user means
- Pay attention to what was just discussed to provide relevant responses

CAPABILITIES:
- Goals: Create, update, and track personal goals
- Habits: Manage daily, weekly, and monthly habits
- Milestones: Break down goals into manageable milestones
- Progress: Log and track progress on goals and habits
- Analysis: Provide insights and recommendations

TOOL USAGE GUIDELINES:
- Always use user_id="123" for all operations
- For goals/habits: Always include user_id parameter
- For milestones: Always include BOTH goal_id AND user_id parameters
- For progress logs: Always include user_id parameter, optionally link to goals/habits
- Use smart searching: Get all items first, then find matches using fuzzy matching
- Never guess exact titles - always use the 2-step approach

SMART SEARCHING RULE:
When user mentions ANY item by name/description:
1. ALWAYS get ALL items first (goals/habits/milestones) with minimal filters
2. THEN analyze results to find matches using fuzzy/partial matching
3. NEVER guess exact titles - always use the 2-step approach

PROGRESS LOG GUIDELINES:
- Progress logs track daily activities, achievements, and challenges
- SMART GOAL/HABIT LINKING: When user logs progress without specifying goal/habit:
  1. FIRST: Get ALL user goals AND habits with minimal filters
  2. THEN: Analyze progress content to find matching goals/habits by keywords
  3. IF MATCH FOUND: Link progress to relevant goal_id or habit_id automatically
  4. IF NO MATCH FOUND: Follow the "ORPHANED PROGRESS STRATEGY"

ORPHANED PROGRESS STRATEGY (when no matching goals/habits exist):
1. DO NOT create progress log without relationships
2. INSTEAD: Suggest creating a relevant goal or habit first
3. Ask user: "I don't see a goal/habit for [activity]. Would you like me to create one?"
4. Offer specific suggestions: "Should I create a goal like 'Learn [topic]' or a habit like 'Practice [activity] daily'?"
5. ONLY create progress log AFTER creating the goal/habit to link to

RESPONSE STRUCTURE:
- action_type: The primary domain (goals, habits, milestones, progress, general)
- summary: Brief summary of what was accomplished
- data: Relevant data from tools (goals, habits, etc.)
- suggestions: Actionable suggestions for the user
- next_steps: Recommended next steps

Always be helpful, encouraging, and provide structured, actionable responses."""

    async def process_request(self, user_input: str, conversation_context: str = "", conversation_summary: str = "", user_id: str = "123") -> ProductivityResponse:
        """Process user request with structured output"""
        try:
            print(f"🔧 **Calling PydanticAI Agent with MCP Tools**")
            print(f"👤 User ID: {user_id}")
            print(f"📝 Prompt: {user_input}")
            if conversation_summary:
                print(f"📋 Conversation summary included: {len(conversation_summary)} characters")
            if conversation_context:
                print(f"💾 Conversation context included: {len(conversation_context)} characters")
            
            # Build the full prompt with conversation context and summary
            prompt_parts = [f"User ID: {user_id}"]
            
            if conversation_summary:
                prompt_parts.append(f"CONVERSATION SUMMARY: {conversation_summary}")
                prompt_parts.append("")  # Empty line for separation
            
            if conversation_context:
                prompt_parts.append(conversation_context)
                prompt_parts.append("")  # Empty line for separation
            
            prompt_parts.append(f"User Request: {user_input}")
            full_prompt = "\n".join(prompt_parts)
            
            # Run the agent with the full prompt
            from langchain_core.messages.utils import count_tokens_approximately
            
            # Count actual tokens using LangChain
            input_tokens = count_tokens_approximately(full_prompt)
            
            result = await self.agent.run(full_prompt)
            
            # Count output tokens
            output_tokens = count_tokens_approximately(str(result))
            
            # Log LLM response details
            logfire.info("llm_response",
                       result_type=type(result).__name__,
                       response_length=len(str(result)),
                       input_tokens=input_tokens,
                       output_tokens=output_tokens,
                       total_tokens=input_tokens + output_tokens)
            
            print(f"📊 **Agent Result Received**")
            print(f"📋 Result Type: {type(result).__name__}")
            
            # Check if result has tool calls or data
            if hasattr(result, 'data') and result.data:
                print(f"🔧 **Tool Calls Made**: {len(result.data) if isinstance(result.data, list) else 'Multiple'}")
                logfire.info("PydanticAI agent made tool calls", 
                           tool_calls_count=len(result.data) if isinstance(result.data, list) else 1)
            
            logfire.info("PydanticAI agent raw result", 
                       result_type=type(result).__name__,
                       result_data=str(result)[:200])
            
            # Parse the result into structured format
            if hasattr(result, 'data'):
                summary = result.data
            elif hasattr(result, 'content'):
                summary = result.content
            else:
                summary = str(result)
            
            response = ProductivityResponse(
                action_type="general",  # Default, will be determined from content
                summary=summary,
                suggestions=[],
                next_steps=[]
            )
            
            print(f"✅ **Response Parsed Successfully**")
            logfire.info("Productivity agent response", 
                        summary=response.summary)
            
            return response
            
        except Exception as e:
            logfire.error("Error processing request", error=str(e))
            return ProductivityResponse(
                action_type="general",
                summary=f"Error processing request: {str(e)}",
                suggestions=["Please try again or rephrase your request"]
            )

class LangGraphOrchestrator:
    """LangGraph orchestrator with PostgreSQL memory"""
    
    def __init__(self, productivity_agent: ProductivityAgent):
        self.productivity_agent = productivity_agent
        self.graph = None
        self.checkpointer = None
    
    async def setup_with_checkpointer(self, checkpointer):
        """Setup LangGraph with provided checkpointer"""
        try:
            # Store the checkpointer
            self.checkpointer = checkpointer
            
            # Create LangGraph workflow
            builder = StateGraph(MessagesState)
            
            # Add nodes
            builder.add_node("productivity_agent", self._call_productivity_agent)
            builder.add_node("format_response", self._format_response)
            
            # Add edges
            builder.add_edge(START, "productivity_agent")
            builder.add_edge("productivity_agent", "format_response")
            builder.add_edge("format_response", END)
            
            # Compile graph with checkpointer
            self.graph = builder.compile(checkpointer=self.checkpointer)
            
            logfire.info("LangGraph orchestrator setup complete")
            
        except Exception as e:
            logfire.error("Error setting up LangGraph", error=str(e))
            raise
    
    async def _call_productivity_agent(self, state: MessagesState) -> Dict[str, Any]:
        """Call the PydanticAI productivity agent with message trimming"""
        try:
            # Get the last user message
            last_message = state["messages"][-1]
            user_input = last_message.content
            
            # Count total messages in memory
            total_messages = len(state["messages"])
            
            print(f"\n🤖 **Running PydanticAI Agent**")
            print(f"📝 Input: {user_input}")
            print(f"💾 Total messages in memory: {total_messages}")
            logfire.info("Running PydanticAI agent", input=user_input, total_messages=total_messages)
            
            # Trim messages if too many to manage context window
            messages_to_use = state["messages"]
            if total_messages > 30:  # Adjust threshold as needed
                print(f"✂️ Trimming messages (was {total_messages})")
                
                # Import trimming utilities
                from langchain_core.messages.utils import (
                    trim_messages,
                    count_tokens_approximately
                )
                
                # Determine max_tokens based on message count
                if total_messages > 100:
                    max_tokens = 2000  # Heavy trimming for very long conversations
                    print("✂️ Heavy trimming (100+ messages)")
                elif total_messages > 50:
                    max_tokens = 4000  # Moderate trimming
                    print("✂️ Moderate trimming (50+ messages)")
                else:
                    max_tokens = 128  # Very low for testing (~5 messages)
                    print("✂️ Light trimming (30+ messages) - TESTING MODE")
                
                # Trim messages
                trimmed_messages = trim_messages(
                    state["messages"],
                    strategy="last",
                    token_counter=count_tokens_approximately,
                    max_tokens=max_tokens,
                    start_on="human",
                    end_on=("human", "tool"),
                )
                
                messages_to_use = trimmed_messages
                print(f"✂️ Trimmed to {len(trimmed_messages)} messages (~{max_tokens} tokens)")
                logfire.info("Messages trimmed", 
                           original_count=total_messages,
                           trimmed_count=len(trimmed_messages),
                           max_tokens=max_tokens)
            
            # Build conversation context and summary for the agent
            conversation_context = self._build_conversation_context(messages_to_use)
            conversation_summary = self._build_conversation_summary(state)
            
            # Process with PydanticAI agent (include conversation context and summary)
            response = await self.productivity_agent.process_request(user_input, conversation_context, conversation_summary)
            
            print(f"✅ **Agent Response Generated**")
            print(f"🎯 Action Type: {response.action_type}")
            print(f"📋 Summary: {response.summary}")
            if response.suggestions:
                print(f"💡 Suggestions: {', '.join(response.suggestions)}")
            
            logfire.info("PydanticAI agent response", 
                       action_type=response.action_type,
                       summary=response.summary,
                       suggestions_count=len(response.suggestions))
            
            # Store response in state
            return {
                "messages": [{
                    "role": "assistant",
                    "content": f"Action: {response.action_type}\nSummary: {response.summary}\nSuggestions: {', '.join(response.suggestions)}"
                }]
            }
            
        except Exception as e:
            print(f"❌ **Agent Error**: {str(e)}")
            logfire.error("Error in productivity agent", error=str(e))
            return {
                "messages": [{
                    "role": "assistant", 
                    "content": f"Error: {str(e)}"
                }]
            }
    
    def _build_conversation_summary(self, state: MessagesState) -> str:
        """Build conversation summary with user context"""
        # For now, return a simple summary - you can enhance this later
        return "User is a perfectionist who gets easily distracted and asks the same questions multiple times. User is enthusiastic about productivity but tends to overcomplicate simple tasks."
    
    def _build_conversation_context(self, messages: List[Any]) -> str:
        """Build conversation context from message history"""
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
    
    async def _format_response(self, state: MessagesState) -> Dict[str, Any]:
        """Format the final response"""
        try:
            print(f"\n🎨 **Formatting Final Response**")
            
            # Get the last message
            last_message = state["messages"][-1]
            
            # Extract content from different message types
            if hasattr(last_message, 'content'):
                content = last_message.content
            elif isinstance(last_message, dict) and "content" in last_message:
                content = last_message["content"]
            else:
                content = str(last_message)
            
            print(f"📝 Content length: {len(content)} characters")
            logfire.info("Formatting response", content_length=len(content))
            
            # Format for display
            formatted_content = f"""
🎯 **Productivity Assistant Response**

{content}

---
*Powered by PydanticAI + MCP + LangGraph + Logfire*
            """
            
            print(f"✅ **Response Formatted Successfully**")
            
            return {
                "messages": [{
                    "role": "assistant",
                    "content": formatted_content
                }]
            }
            
        except Exception as e:
            print(f"❌ **Formatting Error**: {str(e)}")
            logfire.error("Error formatting response", error=str(e))
            return state
    
    async def process(self, user_input: str, thread_id: str = "123") -> Dict[str, Any]:
        """Process user input through the orchestrated workflow"""
        with logfire.span("langgraph_process", user_input=user_input, thread_id=thread_id):
            try:
                print(f"\n🔄 **Starting LangGraph Process**")
                print(f"🧵 Thread ID: {thread_id}")
                print(f"📝 User Input: {user_input}")
                print(f"💾 Loading conversation history from PostgreSQL...")
                
                logfire.info("Starting LangGraph process", 
                           user_input=user_input, 
                           thread_id=thread_id)
                
                result = await self.graph.ainvoke(
                    {"messages": [{"role": "user", "content": user_input}]},
                    config={"thread_id": thread_id}
                )
                
                print(f"✅ **LangGraph Process Complete**")
                print(f"📊 Messages in result: {len(result.get('messages', []))}")
                
                logfire.info("LangGraph process completed", 
                           result_messages_count=len(result.get('messages', [])))
                
                return result
                
            except Exception as e:
                print(f"❌ **LangGraph Process Error**: {str(e)}")
                logfire.error("Error processing through LangGraph", error=str(e))
                raise

async def run_main_loop(orchestrator, productivity_agent, thread_id: str, use_memory: bool = False):
    """Run the main interaction loop"""
    # Main interaction loop
    print("\n🚀 **PydanticAI + MCP + LangGraph Productivity Assistant** 🚀")
    print("=" * 60)
    print("🎯 I can help you manage your goals, habits, milestones, and progress!")
    print("📊 All interactions are traced with Logfire")
    if use_memory:
        print("💾 Conversation history is stored in memory (no persistence)")
    else:
        print("💾 Conversation history is stored in PostgreSQL")
    print("🔧 Powered by PydanticAI for structured responses")
    if not use_memory:
        print("💡 Type 'check memory' to verify LangGraph memory is working")
    print("=" * 60)
    
    # Use async context manager for the agent to manage MCP connections
    async with productivity_agent.agent:
        conversation_count = 0
        
        while True:
            user_input = input("\n💬 What would you like to do? → ")
            
            if user_input.strip().lower() in ["exit", "quit"]:
                print("👋 Goodbye! Keep working on your productivity goals! 🎯")
                break
            
            # Special command to check memory (only for PostgreSQL)
            if not use_memory and user_input.strip().lower() == "check memory":
                try:
                    await check_langgraph_memory(orchestrator.checkpointer, thread_id)
                except Exception as e:
                    print(f"❌ Memory check failed: {str(e)}")
                continue
            
            conversation_count += 1
            
            try:
                logfire.info("Processing user input", input=user_input)
                
                # Process through LangGraph orchestrator
                result = await orchestrator.process(user_input, thread_id, thread_id)
                
                # Display result with better formatting
                print("\n" + "=" * 60)
                
                # Handle different result structures
                if isinstance(result, dict) and "messages" in result:
                    last_message = result["messages"][-1]
                    if hasattr(last_message, 'content'):
                        content = last_message.content
                    elif isinstance(last_message, dict) and "content" in last_message:
                        content = last_message["content"]
                    else:
                        content = str(last_message)
                    
                    # Clean up the content formatting
                    if content.startswith("🎯 **Productivity Assistant Response**"):
                        # Remove the wrapper formatting since we're already in a formatted context
                        lines = content.split('\n')
                        # Skip the first few lines and get the actual content
                        actual_content = '\n'.join(lines[2:-3]) if len(lines) > 5 else content
                        print(actual_content.strip())
                    else:
                        print(content)
                else:
                    print(str(result))
                
                print("=" * 60)
                
            except Exception as e:
                logfire.error("Error processing user input", error=str(e))
                print(f"❌ Error: {str(e)}")

async def check_langgraph_memory(checkpointer, thread_id: str):
    """Check LangGraph memory to verify conversation history is being saved"""
    try:
        print("\n🔍 **Checking LangGraph Memory**")
        print("=" * 50)
        
        # Get the latest checkpoint
        checkpoint = await checkpointer.aget_tuple({"configurable": {"thread_id": thread_id}})
        
        if checkpoint:
            print(f"✅ Found checkpoint for thread: {thread_id}")
            
            # Access checkpoint data safely
            try:
                # Get version from checkpoint data
                if hasattr(checkpoint, 'checkpoint') and hasattr(checkpoint.checkpoint, 'get'):
                    version = checkpoint.checkpoint.get('v', 'Unknown')
                    print(f"📊 Checkpoint version: {version}")
                    
                    # Get timestamp
                    timestamp = checkpoint.checkpoint.get('ts', 'Unknown')
                    print(f"🕒 Timestamp: {timestamp}")
                    
                    # Count messages
                    messages = checkpoint.checkpoint.get('channel_values', {}).get('messages', [])
                    print(f"💬 Total messages in memory: {len(messages)}")
                    
                    # Show recent messages
                    if messages:
                        print("\n📝 **Recent Messages:**")
                        for i, msg in enumerate(messages[-3:], 1):  # Show last 3 messages
                            if isinstance(msg, dict):
                                msg_type = msg.get('type', 'unknown')
                                content = msg.get('content', 'No content')[:100]
                            else:
                                msg_type = getattr(msg, 'type', 'unknown')
                                content = getattr(msg, 'content', 'No content')[:100]
                            print(f"  {i}. {msg_type}: {content}...")
                else:
                    print(f"📊 Checkpoint data: Unable to access structure")
                    
            except Exception as e:
                print(f"❌ Error accessing checkpoint data: {str(e)}")
            
            # Check if we have multiple checkpoints (conversation history)
            try:
                all_checkpoints = []
                async for checkpoint in checkpointer.alist({"configurable": {"thread_id": thread_id}}):
                    all_checkpoints.append(checkpoint)
                print(f"📚 Total checkpoints for this thread: {len(all_checkpoints)}")
            except Exception as e:
                print(f"📚 Total checkpoints: Error accessing - {str(e)}")
            
            # Count PostgreSQL records if possible
            try:
                await count_postgresql_records()
            except Exception as e:
                print(f"⚠️ Could not count PostgreSQL records: {str(e)}")
            
        else:
            print(f"❌ No checkpoint found for thread: {thread_id}")
            print("💡 This might be the first conversation or memory isn't working")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error checking memory: {str(e)}")
        logfire.error("Error checking LangGraph memory", error=str(e))

async def count_postgresql_records():
    """Count records in PostgreSQL LangGraph tables"""
    try:
        import psycopg
        from dotenv import load_dotenv
        
        load_dotenv()
        database_url = os.getenv("PGURL")
        
        if not database_url:
            print("⚠️ No PGURL found for PostgreSQL record counting")
            return
        
        conn = await psycopg.AsyncConnection.connect(database_url)
        
        async with conn.cursor() as cur:
            # Count checkpoints
            await cur.execute("SELECT COUNT(*) FROM checkpoints")
            checkpoint_count = await cur.fetchone()
            
            # Count checkpoint blobs
            await cur.execute("SELECT COUNT(*) FROM checkpoint_blobs")
            blob_count = await cur.fetchone()
            
            # Count checkpoint writes
            await cur.execute("SELECT COUNT(*) FROM checkpoint_writes")
            write_count = await cur.fetchone()
            
            print(f"📊 **PostgreSQL Record Counts:**")
            print(f"  - Checkpoints: {checkpoint_count[0] if checkpoint_count else 0}")
            print(f"  - Blobs: {blob_count[0] if blob_count else 0}")
            print(f"  - Writes: {write_count[0] if write_count else 0}")
        
        await conn.close()
        
    except Exception as e:
        print(f"⚠️ Error counting PostgreSQL records: {str(e)}")

async def main():
    """Main function to run the PydanticAI + MCP + LangGraph system"""
    
    # Initialize Logfire
    logfire.info("Starting PydanticAI + MCP + LangGraph system")
    
    try:
        # Create productivity agent with MCP integration
        logfire.info("Creating productivity agent with MCP...")
        productivity_agent = ProductivityAgent()
        
        print("✅ MCP Server configured for goalgetter")
        print("✅ PydanticAI agent created with MCP toolsets")
        
        # Setup LangGraph orchestrator with PostgreSQL
        database_url = os.getenv("PGURL")
        if not database_url:
            raise ValueError("PGURL environment variable not set")
        
        # Try PostgreSQL first, fallback to memory if it fails
        try:
            # Use async context manager for PostgreSQL checkpointer
            async with AsyncPostgresSaver.from_conn_string(database_url) as checkpointer:
                print("✅ PostgreSQL connection established")
                
                # Create orchestrator with checkpointer
                orchestrator = LangGraphOrchestrator(productivity_agent)
                await orchestrator.setup_with_checkpointer(checkpointer)
                
                logfire.info("System initialization complete with PostgreSQL")
                
                # Run the main loop with PostgreSQL
                await run_main_loop(orchestrator, productivity_agent, thread_id="123")
                
        except Exception as e:
            print(f"⚠️ PostgreSQL connection failed: {str(e)}")
            print("🔄 Falling back to in-memory storage...")
            logfire.warning("PostgreSQL failed, falling back to memory", error=str(e))
            
            # Fallback to memory-only mode
            from langgraph.checkpoint.memory import MemorySaver
            memory_checkpointer = MemorySaver()
            
            # Create orchestrator with memory checkpointer
            orchestrator = LangGraphOrchestrator(productivity_agent)
            await orchestrator.setup_with_checkpointer(memory_checkpointer)
            
            print("✅ Using in-memory storage (no persistence)")
            logfire.info("System initialization complete with memory fallback")
            
            # Run the main loop with memory
            await run_main_loop(orchestrator, productivity_agent, thread_id="123", use_memory=True)
    
    except Exception as e:
        logfire.error("System initialization failed", error=str(e))
        print(f"❌ System error: {str(e)}")
        raise
    
    finally:
        # Cleanup is handled by async context managers
        logfire.info("System shutdown complete")

def run_client():
    """Run the client"""
    asyncio.run(main())

if __name__ == "__main__":
    run_client()

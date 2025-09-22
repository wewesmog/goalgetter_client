"""
Core AI agents and orchestration logic.

This module contains the main ProductivityAgent and LangGraphOrchestrator classes.
"""

import asyncio
import sys
from typing import Dict, Any

# Core imports
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from langgraph.graph import StateGraph, MessagesState, START, END

# Local imports
from src.models.responses import ProductivityResponse
from src.services.mcp_service import create_mcp_server
from src.services.memory_service import MemoryService
from src.services.conversation_service import ConversationService
from src.utils.logging import setup_logfire
from src.utils.message_utils import trim_messages
from config.settings import settings
from config.prompts import get_system_prompt
import logfire


class ProductivityAgent:
    """PydanticAI agent for productivity management."""
    
    def __init__(self):
        # Create MCP server (local or remote)
        self.mcp_server = create_mcp_server()
        
        # Check if we have a remote HTTP client or local stdio client
        from src.services.mcp_service import HTTPMCPClient
        self.is_remote_mcp = isinstance(self.mcp_server, HTTPMCPClient)
        
        if self.is_remote_mcp:
            # For remote MCP, create agent without toolsets (we'll handle tools manually)
            self.agent = Agent(
                model=OpenAIChatModel("gpt-4o-mini"),
                system_prompt=get_system_prompt()
            )
        else:
            # For local MCP, use standard PydanticAI integration
            self.agent = Agent(
                model=OpenAIChatModel("gpt-4o-mini"),
                system_prompt=get_system_prompt(),
                toolsets=[self.mcp_server]
            )
        
        # Store user_id for tool context (not in LLM prompt)
        self.user_id = None
    
    async def process_request(self, user_input: str, conversation_context: str = "", conversation_summary: str = "", user_id: str = "123") -> ProductivityResponse:
        """Process user request with structured output."""
        try:
            # Store user_id for tool context (not in LLM prompt)
            self.user_id = user_id
            
            print(f"🔧 **Calling PydanticAI Agent with MCP Tools**")
            print(f"👤 User ID: {user_id} (stored in agent context, not in LLM prompt)")
            print(f"📝 Prompt: {user_input}")
            if conversation_summary:
                print(f"📋 Conversation summary included: {len(conversation_summary)} characters")
            if conversation_context:
                print(f"💾 Conversation context included: {len(conversation_context)} characters")
            
            # Build the full prompt with user_id in tool context only
            prompt_parts = []
            
            # Add user_id for tool calls (not for general conversation)
            prompt_parts.append(f"TOOL CONTEXT: user_id={user_id}")
            prompt_parts.append("")
            
            if conversation_summary:
                prompt_parts.append(f"CONVERSATION SUMMARY: {conversation_summary}")
                prompt_parts.append("")
            
            if conversation_context:
                prompt_parts.append(conversation_context)
                prompt_parts.append("")
            
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
                action_type="general",
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
    """LangGraph orchestrator with PostgreSQL memory."""
    
    def __init__(self, productivity_agent: ProductivityAgent):
        self.productivity_agent = productivity_agent
        self.graph = None
        self.checkpointer = None
        self.conversation_service = ConversationService()
    
    async def setup_with_checkpointer(self, checkpointer):
        """Setup LangGraph with provided checkpointer."""
        try:
            print(f"🔧 Setting up LangGraph orchestrator with checkpointer: {type(checkpointer)}")
            
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
            print(f"🔧 Compiling LangGraph with checkpointer...")
            self.graph = builder.compile(checkpointer=self.checkpointer)
            print(f"✅ LangGraph compiled successfully: {type(self.graph)}")
            
            logfire.info("LangGraph orchestrator setup complete")
            
        except Exception as e:
            print(f"❌ LangGraph setup failed: {str(e)}")
            logfire.error("Error setting up LangGraph", error=str(e))
            raise
    
    async def _call_productivity_agent(self, state: MessagesState, config: dict = None) -> Dict[str, Any]:
        """Call the PydanticAI productivity agent with message trimming."""
        try:
            # Get the last user message
            last_message = state["messages"][-1]
            user_input = last_message.content
            
            # Get user_id from config
            if config and "configurable" in config:
                user_id = config["configurable"].get("user_id", "123")
            else:
                user_id = "123"
            
            # Count total messages in memory
            total_messages = len(state["messages"])
            
            print(f"\n🤖 **Running PydanticAI Agent**")
            print(f"📝 Input: {user_input}")
            print(f"💾 Total messages in memory: {total_messages}")
            logfire.info("Running PydanticAI agent", input=user_input, total_messages=total_messages)
            
            # Trim messages if too many to manage context window
            messages_to_use = state["messages"]
            if total_messages > settings.max_messages_before_trimming:
                print(f"✂️ Trimming messages (was {total_messages})")
                
                messages_to_use = trim_messages(state["messages"], total_messages)
                print(f"✂️ Trimmed to {len(messages_to_use)} messages")
                logfire.info("Messages trimmed", 
                           original_count=total_messages,
                           trimmed_count=len(messages_to_use))
            
            # Build conversation context and summary for the agent
            conversation_context = self.conversation_service.build_conversation_context(messages_to_use)
            conversation_summary = self.conversation_service.build_conversation_summary(state)
            
            # Process with PydanticAI agent
            response = await self.productivity_agent.process_request(user_input, conversation_context, conversation_summary, user_id)
            
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
    
    async def _format_response(self, state: MessagesState) -> Dict[str, Any]:
        """Format the final response."""
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
    
    async def process(self, user_input: str, thread_id: str = "123", user_id: str = "123") -> Dict[str, Any]:
        """Process user input through the orchestrated workflow."""
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
                    config={"configurable": {"thread_id": thread_id, "user_id": user_id}}
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
    """Run the main interaction loop."""
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
                    memory_service = MemoryService()
                    await memory_service.check_memory_status(orchestrator.checkpointer, thread_id)
                except Exception as e:
                    print(f"❌ Memory check failed: {str(e)}")
                continue
            
            conversation_count += 1
            
            try:
                logfire.info("Processing user input", input=user_input)
                
                # Process through LangGraph orchestrator
                result = await orchestrator.process(user_input, thread_id)
                
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


async def main():
    """Main function to run the PydanticAI + MCP + LangGraph system."""
    
    # Initialize Logfire
    setup_logfire()
    logfire.info("Starting PydanticAI + MCP + LangGraph system")
    
    try:
        # Create productivity agent with MCP integration
        logfire.info("Creating productivity agent with MCP...")
        productivity_agent = ProductivityAgent()
        
        print("✅ MCP Server configured for goalgetter")
        print("✅ PydanticAI agent created with MCP toolsets")
        
        # Setup memory service
        memory_service = MemoryService()
        
        # Try PostgreSQL first, fallback to memory if it fails
        try:
            # Use async context manager for PostgreSQL checkpointer
            async with memory_service.setup_postgres_checkpointer() as checkpointer:
                print("✅ PostgreSQL connection established")
                
                # Create orchestrator with checkpointer
                orchestrator = LangGraphOrchestrator(productivity_agent)
                await orchestrator.setup_with_checkpointer(checkpointer)
                
                logfire.info("System initialization complete with PostgreSQL")
                
                # Run the main loop with PostgreSQL
                await run_main_loop(orchestrator, productivity_agent, thread_id=settings.thread_id)
                
        except Exception as e:
            print(f"⚠️ PostgreSQL connection failed: {str(e)}")
            print("🔄 Falling back to in-memory storage...")
            logfire.warning("PostgreSQL failed, falling back to memory", error=str(e))
            
            # Fallback to memory-only mode
            memory_checkpointer = memory_service.setup_memory_checkpointer()
            
            # Create orchestrator with memory checkpointer
            orchestrator = LangGraphOrchestrator(productivity_agent)
            await orchestrator.setup_with_checkpointer(memory_checkpointer)
            
            print("✅ Using in-memory storage (no persistence)")
            logfire.info("System initialization complete with memory fallback")
            
            # Run the main loop with memory
            await run_main_loop(orchestrator, productivity_agent, thread_id=settings.thread_id, use_memory=True)
    
    except Exception as e:
        logfire.error("System initialization failed", error=str(e))
        print(f"❌ System error: {str(e)}")
        raise
    
    finally:
        # Cleanup is handled by async context managers
        logfire.info("System shutdown complete")


def run_client():
    """Run the client."""
    asyncio.run(main())

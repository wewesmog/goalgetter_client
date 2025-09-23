"""
LangGraph orchestration for agent workflows.

This module contains the LangGraph orchestrator for managing agent workflows and state.
"""

import asyncio
import sys
from typing import Dict, Any

# Core imports
from langgraph.graph import StateGraph, MessagesState, START, END

# Local imports
from .productivity_agent import ProductivityAgent
from src.models.responses import ProductivityResponse
from src.services.memory_service import MemoryService
from src.services.conversation_service import ConversationService
from src.utils.logging import setup_logfire
from src.utils.message_utils import trim_messages
from config.settings import settings
import logfire


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
            
            # Store response in state - use only the summary for clean conversational flow
            # The summary should contain the main conversational response
            conversational_content = response.summary
            
            # Add suggestions if they exist and are meaningful
            if response.suggestions and any(suggestion.strip() for suggestion in response.suggestions):
                conversational_content += "\n\n" + "\n".join(response.suggestions)
            
            return {
                "messages": [{
                    "role": "assistant",
                    "content": conversational_content
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

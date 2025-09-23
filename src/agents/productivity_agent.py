"""
PydanticAI Productivity Agent.

This module contains the ProductivityAgent class for managing goals, habits, milestones, and progress logs.
"""

from typing import Dict, Any, List
import logfire
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from langchain_core.messages.utils import count_tokens_approximately

from src.services.mcp_service import create_mcp_server
from src.models.responses import ProductivityResponse
from config.prompts import get_system_prompt


class ProductivityAgent:
    """PydanticAI agent for productivity management."""
    
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
        return get_system_prompt()

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

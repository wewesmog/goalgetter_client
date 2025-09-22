"""
Memory and checkpoint management service.

This module handles PostgreSQL checkpointer setup and memory operations.
"""

import os
import asyncio
import psycopg
from typing import Optional
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.memory import MemorySaver
import logfire


class MemoryService:
    """Service for managing conversation memory and checkpoints."""
    
    def __init__(self):
        self.checkpointer: Optional[AsyncPostgresSaver] = None
        # Import settings here to avoid circular imports
        from config.settings import settings
        self.database_url = settings.database_url
    
    async def setup_postgres_checkpointer(self) -> AsyncPostgresSaver:
        """Setup PostgreSQL checkpointer with connection string."""
        try:
            print(f"🔧 Setting up PostgreSQL checkpointer with URL: {self.database_url[:50]}...")
            # Use the same approach as mcp_client_pydantic.py
            checkpointer = await AsyncPostgresSaver.from_conn_string(self.database_url)
            print(f"✅ PostgreSQL checkpointer created: {type(checkpointer)}")
            logfire.info("PostgreSQL checkpointer setup complete")
            return checkpointer
        except Exception as e:
            print(f"❌ PostgreSQL checkpointer setup failed: {str(e)}")
            logfire.error("Failed to setup PostgreSQL checkpointer", error=str(e))
            raise
    
    def setup_memory_checkpointer(self) -> MemorySaver:
        """Setup in-memory checkpointer as fallback."""
        logfire.info("Using in-memory checkpointer as fallback")
        return MemorySaver()
    
    async def check_memory_status(self, checkpointer, thread_id: str) -> None:
        """Check LangGraph memory status and display information."""
        try:
            print("\n🔍 **Checking LangGraph Memory**")
            print("=" * 50)
            
            # Get the latest checkpoint
            checkpoint = await checkpointer.aget_tuple({"configurable": {"thread_id": thread_id}})
            
            if checkpoint:
                print(f"✅ Found checkpoint for thread: {thread_id}")
                
                # Access checkpoint data safely
                try:
                    if hasattr(checkpoint, 'checkpoint') and hasattr(checkpoint.checkpoint, 'get'):
                        version = checkpoint.checkpoint.get('v', 'Unknown')
                        print(f"📊 Checkpoint version: {version}")
                        
                        timestamp = checkpoint.checkpoint.get('ts', 'Unknown')
                        print(f"🕒 Timestamp: {timestamp}")
                        
                        messages = checkpoint.checkpoint.get('channel_values', {}).get('messages', [])
                        print(f"💬 Total messages in memory: {len(messages)}")
                        
                        # Show recent messages
                        if messages:
                            print("\n📝 **Recent Messages:**")
                            for i, msg in enumerate(messages[-3:], 1):
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
                
                # Check total checkpoints
                try:
                    all_checkpoints = []
                    async for checkpoint in checkpointer.alist({"configurable": {"thread_id": thread_id}}):
                        all_checkpoints.append(checkpoint)
                    print(f"📚 Total checkpoints for this thread: {len(all_checkpoints)}")
                except Exception as e:
                    print(f"📚 Total checkpoints: Error accessing - {str(e)}")
                
                # Count PostgreSQL records
                await self._count_postgresql_records()
                
            else:
                print(f"❌ No checkpoint found for thread: {thread_id}")
                print("💡 This might be the first conversation or memory isn't working")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error checking memory: {str(e)}")
            logfire.error("Error checking LangGraph memory", error=str(e))
    
    async def _count_postgresql_records(self) -> None:
        """Count records in PostgreSQL LangGraph tables."""
        try:
            conn = await psycopg.AsyncConnection.connect(self.database_url)
            
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

"""
User management service for Telegram users.

This module handles user creation, updates, and retrieval for Telegram users.
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
import psycopg
from config.settings import settings
import logfire


class UserService:
    """Service for managing Telegram users."""
    
    def __init__(self):
        self.database_url = settings.database_url
    
    async def get_or_create_user_async(self, telegram_user: Dict[str, Any]) -> Dict[str, Any]:
        """Get user or create if doesn't exist - optimized for Telegram."""
        user_id = str(telegram_user["id"])
        
        try:
            # Try to get user first (fast path)
            user = await self.get_user(user_id)
            logfire.info("User found", user_id=user_id)
            return user
        except UserNotFound:
            # Create user in background (don't wait)
            asyncio.create_task(self.create_user_background(telegram_user))
            
            # Return default user immediately
            return {
                "user_id": user_id,
                "first_name": telegram_user.get("first_name", ""),
                "last_name": telegram_user.get("last_name"),
                "username": telegram_user.get("username"),
                "language_code": telegram_user.get("language_code"),
                "timezone": "UTC",
                "created_at": datetime.now().isoformat(),
                "status": "pending_creation"
            }
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID."""
        try:
            conn = await psycopg.AsyncConnection.connect(self.database_url)
            
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT user_id, first_name, last_name, username, language_code, timezone, created_at FROM users WHERE user_id = %s",
                    (user_id,)
                )
                result = await cur.fetchone()
                
                if not result:
                    raise UserNotFound(f"User {user_id} not found")
                
                return {
                    "user_id": str(result[0]),
                    "first_name": result[1],
                    "last_name": result[2],
                    "username": result[3],
                    "language_code": result[4],
                    "timezone": result[5],
                    "created_at": result[6].isoformat() if result[6] else None
                }
        finally:
            await conn.close()
    
    async def create_user_background(self, telegram_user: Dict[str, Any]):
        """Create user in background without blocking chat flow."""
        user_id = str(telegram_user["id"])
        
        try:
            await self.create_user(telegram_user)
            logfire.info("User created successfully in background", user_id=user_id)
        except Exception as e:
            logfire.error("Background user creation failed", user_id=user_id, error=str(e))
    
    async def create_user(self, telegram_user: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user."""
        user_id = str(telegram_user["id"])
        
        try:
            conn = await psycopg.AsyncConnection.connect(self.database_url)
            
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO users (user_id, first_name, last_name, username, language_code, timezone, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        username = EXCLUDED.username,
                        language_code = EXCLUDED.language_code
                    RETURNING user_id, first_name, last_name, username, language_code, timezone, created_at
                    """,
                    (
                        user_id,
                        telegram_user.get("first_name", ""),
                        telegram_user.get("last_name"),
                        telegram_user.get("username"),
                        telegram_user.get("language_code"),
                        "UTC",  # Default timezone
                        datetime.now()
                    )
                )
                
                result = await cur.fetchone()
                await conn.commit()
                
                return {
                    "user_id": str(result[0]),
                    "first_name": result[1],
                    "last_name": result[2],
                    "username": result[3],
                    "language_code": result[4],
                    "timezone": result[5],
                    "created_at": result[6].isoformat() if result[6] else None
                }
        finally:
            await conn.close()
    
    async def update_user_timezone(self, user_id: str, timezone: str):
        """Update user's timezone."""
        try:
            conn = await psycopg.AsyncConnection.connect(self.database_url)
            
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE users SET timezone = %s WHERE user_id = %s",
                    (timezone, user_id)
                )
                await conn.commit()
                
            logfire.info("User timezone updated", user_id=user_id, timezone=timezone)
        except Exception as e:
            logfire.error("Failed to update user timezone", user_id=user_id, error=str(e))
        finally:
            await conn.close()


class UserNotFound(Exception):
    """Exception raised when user is not found."""
    pass


"""
Configuration settings for the productivity assistant.

This module handles environment variables and application configuration.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    
    # Database Configuration
    database_url: str = Field("postgresql://localhost:5432/goalgetter", env="DATABASE_URL")
    
    # Logfire Configuration
    logfire_token: Optional[str] = Field(None, env="LOGFIRE_TOKEN")
    
    # Application Configuration
    service_name: str = Field("pydantic-productivity-assistant", env="SERVICE_NAME")
    service_version: str = Field("1.0.0", env="SERVICE_VERSION")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # MCP Server Configuration
    mcp_server_mode: str = Field("local", env="MCP_SERVER_MODE")  # "local" or "remote"
    mcp_server_path: str = Field("D:\\goalgetter", env="MCP_SERVER_PATH")
    mcp_server_url: str = Field("", env="MCP_SERVER_URL")  # For remote server
    mcp_server_timeout: int = Field(30, env="MCP_SERVER_TIMEOUT")
    
    # User Configuration
    default_user_id: str = Field("123", env="DEFAULT_USER_ID")
    thread_id: str = Field("123", env="THREAD_ID")
    
    # Performance Configuration
    max_messages_before_trimming: int = Field(30, env="MAX_MESSAGES_BEFORE_TRIMMING")
    max_tokens_light_trimming: int = Field(128, env="MAX_TOKENS_LIGHT_TRIMMING")
    max_tokens_moderate_trimming: int = Field(4000, env="MAX_TOKENS_MODERATE_TRIMMING")
    max_tokens_heavy_trimming: int = Field(2000, env="MAX_TOKENS_HEAVY_TRIMMING")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()

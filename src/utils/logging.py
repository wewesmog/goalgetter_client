"""
Logging and observability setup.

This module handles Logfire configuration and logging setup.
"""

import logfire
from config.settings import settings


def setup_logfire() -> None:
    """Initialize Logfire tracing with proper configuration."""
    logfire.configure(
        service_name=settings.service_name,
        service_version=settings.service_version,
        console=logfire.ConsoleConfig() if settings.debug else None,
        send_to_logfire=bool(settings.logfire_token)
    )
    logfire.instrument_pydantic_ai()


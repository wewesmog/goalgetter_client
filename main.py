"""
Main entry point for the Goalgetter Client FastAPI application.

This file serves as the entry point for Railway deployment.
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the FastAPI app from src.api.main
from src.api.main import app

# Export the app for uvicorn
__all__ = ['app']

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Railway sets this)
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting Goalgetter Client on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

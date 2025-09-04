#!/usr/bin/env python3
"""
FloatChat Server Runner

A simple script to start the FloatChat FastAPI server with proper Python path configuration.
This eliminates the need for the complex command and allows direct uvicorn usage.

Usage:
    python run_server.py
    OR
    uvicorn run_server:app --host 0.0.0.0 --port 8001
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
backend_dir = Path(__file__).parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

# Now import the app
from main import app

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print(f"Starting FloatChat API server on {host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=log_level,
        reload=False  # Set to True for development with auto-reload
    )
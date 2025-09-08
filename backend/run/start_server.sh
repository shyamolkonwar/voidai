#!/bin/bash
# FloatChat Server Startup Script
# Simple way to start the server without complex commands

echo "Starting FloatChat API Server..."
cd "$(dirname "$0")"

# Use the new run_server.py script
python run_server.py
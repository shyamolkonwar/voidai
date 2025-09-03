"""
FloatChat Backend Package
========================

Main package for FloatChat backend system containing:
- RAG Core: AI-powered text-to-SQL generation
- Database Manager: PostgreSQL connection and query execution
- Main API: FastAPI application server

Author: FloatChat Backend System
"""

# Version information
__version__ = "1.0.0"
__author__ = "FloatChat Backend System"

# Import main components for easier access
from .rag_core import FloatChatRAGCore, QueryResult
from .db_manager import FloatChatDBManager, QueryExecutionResult

__all__ = [
    "FloatChatRAGCore",
    "QueryResult", 
    "FloatChatDBManager",
    "QueryExecutionResult"
]

"""
FloatChat FastAPI Application
=============================

Main API server for FloatChat MVP.
Provides REST endpoints for natural language to SQL query processing.

Author: FloatChat Backend System
"""

import logging
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import time
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from src.rag_core import FloatChatRAGCore, QueryResult
from src.db_manager import FloatChatDBManager, QueryExecutionResult
from src.chat_history_manager import ChatHistoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables first
load_dotenv()

# Configuration from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/floatchat")
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "http://localhost:11434/api/generate")
MAX_QUERY_TIME = int(os.getenv("MAX_QUERY_TIME", "30"))

# Global instances (will be initialized in lifespan)
rag_core: Optional[FloatChatRAGCore] = None
db_manager: Optional[FloatChatDBManager] = None
chat_history_manager: Optional[ChatHistoryManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    global rag_core, db_manager, chat_history_manager

    logger.info("Starting FloatChat API server...")

    try:
        # Initialize database manager
        logger.info("Initializing database manager...")
        db_manager = FloatChatDBManager(DATABASE_URL)

        # Test database connection
        if not db_manager.test_connection():
            raise Exception("Failed to connect to PostgreSQL database")
        logger.info("Database connection established")

        # Initialize chat history manager
        logger.info("Initializing chat history manager...")
        chat_history_manager = ChatHistoryManager(db_manager)
        logger.info("Chat history manager initialized")

        # Initialize RAG core
        logger.info("Initializing RAG core...")
        rag_core = FloatChatRAGCore(
            chroma_host=CHROMA_HOST,
            chroma_port=CHROMA_PORT,
            llm_endpoint=LLM_ENDPOINT
        )
        logger.info("RAG core initialized")

        logger.info("FloatChat API server startup complete")

    except Exception as e:
        logger.error(f"Failed to initialize FloatChat API server: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down FloatChat API server...")

    if db_manager:
        db_manager.close()
        logger.info("Database connections closed")

    logger.info("FloatChat API server shutdown complete")

# Initialize FastAPI app
app = FastAPI(
    title="FloatChat API",
    description="Natural Language to SQL API for ARGO Float Data",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for natural language queries"""
    query: str = Field(..., description="Natural language query", min_length=1, max_length=1000)
    session_id: Optional[str] = Field(default=None, description="Chat session ID for context awareness")
    include_context: bool = Field(default=True, description="Include retrieved context in response")
    max_results: int = Field(default=100, description="Maximum number of result rows", ge=1, le=1000)

class QueryResponse(BaseModel):
    """Response model for query results"""
    success: bool = Field(..., description="Whether the query was successful")
    data: list = Field(..., description="Query result data")
    sql_query: str = Field(..., description="Generated SQL query")
    row_count: int = Field(..., description="Number of rows returned")
    confidence_score: float = Field(..., description="Confidence score for the query")
    execution_time: float = Field(..., description="Total execution time in seconds")
    reasoning: str = Field(..., description="Explanation of the query generation")
    error_message: Optional[str] = Field(default=None, description="Error message if query failed")
    context: Optional[list] = Field(default=None, description="Retrieved context documents")
    type: str = Field(default="text", description="Response type: map, table, or text")
    summary: Optional[str] = Field(default=None, description="Summary text for display")

class StatusResponse(BaseModel):
    """Response model for status endpoint"""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    database_connected: bool = Field(..., description="Database connection status")
    rag_initialized: bool = Field(..., description="RAG system initialization status")

# Dependency injection for components
async def get_rag_core() -> FloatChatRAGCore:
    """Dependency for RAG core instance"""
    if rag_core is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG core not initialized"
        )
    return rag_core

async def get_db_manager() -> FloatChatDBManager:
    """Dependency for database manager instance"""
    if db_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database manager not initialized"
        )
    return db_manager

async def get_chat_history_manager() -> ChatHistoryManager:
    """Dependency for chat history manager instance"""
    if chat_history_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat history manager not initialized"
        )
    return chat_history_manager

# Session management endpoints
class SessionCreateResponse(BaseModel):
    """Response model for session creation"""
    session_id: str = Field(..., description="New session UUID")
    created_at: str = Field(..., description="Session creation timestamp")

class SessionHistoryResponse(BaseModel):
    """Response model for session history"""
    session_id: str = Field(..., description="Session UUID")
    messages: List[Dict[str, Any]] = Field(..., description="Chat messages")
    message_count: int = Field(..., description="Number of messages in session")

class SessionListResponse(BaseModel):
    """Response model for session list"""
    sessions: List[Dict[str, Any]] = Field(..., description="List of chat sessions")

@app.post("/api/v1/sessions", response_model=SessionCreateResponse)
async def create_session(
    chat_manager: ChatHistoryManager = Depends(get_chat_history_manager)
):
    """
    Create a new chat session.
    
    Returns:
        New session ID that can be used for subsequent queries
    """
    session_id = chat_manager.create_session()
    return SessionCreateResponse(
        session_id=session_id,
        created_at=datetime.now().isoformat()
    )

@app.get("/api/v1/sessions", response_model=SessionListResponse)
async def get_all_sessions(
    chat_manager: ChatHistoryManager = Depends(get_chat_history_manager)
):
    """
    Get all chat sessions.
    
    Returns:
        List of all chat sessions with their metadata
    """
    sessions = chat_manager.get_all_sessions()
    return SessionListResponse(sessions=sessions)

@app.get("/api/v1/sessions/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    chat_manager: ChatHistoryManager = Depends(get_chat_history_manager)
):
    """
    Get chat history for a specific session.
    
    Args:
        session_id: UUID of the chat session
        
    Returns:
        Complete chat history for the session
    """
    messages = chat_manager.get_recent_history(session_id, limit=50)  # Get up to 50 messages
    return SessionHistoryResponse(
        session_id=session_id,
        messages=messages,
        message_count=len(messages)
    )

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic API information"""
    return {
        "message": "FloatChat API",
        "description": "Natural Language to SQL API for ARGO Float Data",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@app.get("/api/v1/status", response_model=StatusResponse)
async def get_status(
    rag: FloatChatRAGCore = Depends(get_rag_core),
    db: FloatChatDBManager = Depends(get_db_manager)
):
    """
    Get API service status and health information.
    """
    try:
        # Test database connection
        db_connected = db.test_connection()

        return StatusResponse(
            status="ok",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            database_connected=db_connected,
            rag_initialized=True
        )

    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service health check failed: {str(e)}"
        )

@app.post("/api/v1/query", response_model=QueryResponse)
async def process_query_v1(
    request: QueryRequest,
    rag: FloatChatRAGCore = Depends(get_rag_core),
    db: FloatChatDBManager = Depends(get_db_manager),
    chat_manager: ChatHistoryManager = Depends(get_chat_history_manager)
):
    """
    Process a natural language query and return SQL results.

    This endpoint orchestrates the complete workflow:
    1. Converts natural language to SQL using RAG
    2. Validates and executes the SQL query
    3. Returns structured results with metadata
    """
    start_time = time.time()

    try:
        logger.info(f"Processing query: {request.query}")

        # Step 1: Handle session context
        conversation_context = None
        if request.session_id:
            # Get conversation history for context
            conversation_context = chat_manager.get_conversation_context(request.session_id)
            logger.info(f"Using conversation context for session {request.session_id}")
        
        # Step 2: Generate SQL using RAG core with conversation context
        logger.info("Generating SQL using RAG core...")
        rag_result: QueryResult = rag.process_query(request.query, conversation_context)

        if not rag_result.sql_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to generate SQL query from natural language input"
            )

        # Step 2: Execute SQL using database manager
        logger.info("Executing SQL query...")
        db_result: QueryExecutionResult = db.execute_query(
            rag_result.sql_query,
            timeout=MAX_QUERY_TIME
        )

        # Step 3: Limit results if necessary
        limited_data = db_result.data[:request.max_results] if db_result.data else []
        actual_row_count = len(limited_data)

        # Step 4: Persist messages to chat history if session exists
        if request.session_id:
            # Persist user message
            chat_manager.add_message(request.session_id, "user", request.query)
            
            # Persist assistant response
            assistant_message = rag_result.reasoning if rag_result.reasoning else "Query processed successfully"
            chat_manager.add_message(request.session_id, "assistant", assistant_message)
            
            # Clean up old messages to keep history manageable
            chat_manager.cleanup_old_messages(request.session_id)

        # Step 4: Calculate total execution time
        total_execution_time = time.time() - start_time

        # Step 5: Prepare response
        response_data = {
            "success": db_result.success,
            "data": limited_data,
            "sql_query": rag_result.sql_query,
            "row_count": actual_row_count,
            "confidence_score": rag_result.confidence_score,
            "execution_time": total_execution_time,
            "reasoning": rag_result.reasoning,
            "error_message": db_result.error_message if not db_result.success else None,
            "type": "table",  # Default to table for API responses
            "summary": rag_result.reasoning
        }

        # Include context if requested
        if request.include_context and rag_result.retrieved_context:
            response_data["context"] = [
                {
                    "content": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                    "metadata": doc["metadata"],
                    "similarity_score": doc["similarity_score"]
                }
                for doc in rag_result.retrieved_context
            ]

        # Log the result
        if db_result.success:
            logger.info(f"Query processed successfully: {actual_row_count} rows, {total_execution_time:.2f}s")
        else:
            logger.warning(f"Query failed: {db_result.error_message}")

        return QueryResponse(**response_data)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error processing query: {str(e)}")
        total_execution_time = time.time() - start_time

        return QueryResponse(
            success=False,
            data=[],
            sql_query="",
            row_count=0,
            confidence_score=0.0,
            execution_time=total_execution_time,
            reasoning="Query processing failed due to internal error",
            error_message=f"Internal server error: {str(e)}",
            type="text",
            summary="Sorry, I encountered an issue processing your query."
        )

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    rag: FloatChatRAGCore = Depends(get_rag_core),
    db: FloatChatDBManager = Depends(get_db_manager),
    chat_manager: ChatHistoryManager = Depends(get_chat_history_manager)
):
    """
    Process a natural language query and return results in frontend-compatible format.
    
    This endpoint provides the response format expected by the Streamlit frontend.
    """
    start_time = time.time()

    try:
        logger.info(f"Processing frontend query: {request.query}")

        # Step 1: Handle session context
        conversation_context = None
        if request.session_id:
            # Get conversation history for context
            conversation_context = chat_manager.get_conversation_context(request.session_id)
            logger.info(f"Using conversation context for session {request.session_id}")
        
        # Step 2: Generate SQL using RAG core with conversation context
        logger.info("Generating SQL using RAG core...")
        rag_result: QueryResult = rag.process_query(request.query, conversation_context)

        if not rag_result.sql_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to generate SQL query from natural language input"
            )

        # Step 2: Execute SQL using database manager
        logger.info("Executing SQL query...")
        db_result: QueryExecutionResult = db.execute_query(
            rag_result.sql_query,
            timeout=MAX_QUERY_TIME
        )

        # Step 3: Limit results if necessary
        limited_data = db_result.data[:request.max_results] if db_result.data else []
        actual_row_count = len(limited_data)

        # Step 4: Calculate total execution time
        total_execution_time = time.time() - start_time

        # Step 5: Determine response type based on data content
        response_type = "text"
        summary_text = rag_result.reasoning
        
        if db_result.success and limited_data:
            # Check if we have geographic data for map display
            has_geo_data = any('latitude' in row and 'longitude' in row for row in limited_data)
            if has_geo_data:
                response_type = "map"
                summary_text = f"Showing {actual_row_count} geographic data points"
            else:
                response_type = "table"
                summary_text = f"Showing {actual_row_count} data rows"

        # Step 6: Persist messages to chat history if session exists
        if request.session_id:
            # Persist user message
            chat_manager.add_message(request.session_id, "user", request.query)
            
            # Persist assistant response
            assistant_message = summary_text if summary_text else "Query processed successfully"
            chat_manager.add_message(request.session_id, "assistant", assistant_message)
            
            # Clean up old messages to keep history manageable
            chat_manager.cleanup_old_messages(request.session_id)

        # Step 7: Prepare response for frontend
        response_data = {
            "success": db_result.success,
            "data": limited_data,
            "sql_query": rag_result.sql_query,
            "row_count": actual_row_count,
            "confidence_score": rag_result.confidence_score,
            "execution_time": total_execution_time,
            "reasoning": rag_result.reasoning,
            "error_message": db_result.error_message if not db_result.success else None,
            "type": response_type,
            "summary": summary_text
        }

        # Include context if requested
        if request.include_context and rag_result.retrieved_context:
            response_data["context"] = [
                {
                    "content": doc["content"][:500] + "..." if len(doc["content"]) > 500 else doc["content"],
                    "metadata": doc["metadata"],
                    "similarity_score": doc["similarity_score"]
                }
                for doc in rag_result.retrieved_context
            ]

        # Log the result
        if db_result.success:
            logger.info(f"Frontend query processed successfully: {actual_row_count} rows, type: {response_type}, {total_execution_time:.2f}s")
        else:
            logger.warning(f"Frontend query failed: {db_result.error_message}")

        return QueryResponse(**response_data)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error processing frontend query: {str(e)}")
        total_execution_time = time.time() - start_time

        return QueryResponse(
            success=False,
            data=[],
            sql_query="",
            row_count=0,
            confidence_score=0.0,
            execution_time=total_execution_time,
            reasoning="Query processing failed due to internal error",
            error_message=f"Internal server error: {str(e)}",
            type="text",
            summary="Sorry, I encountered an issue processing your query."
        )

@app.get("/api/v1/schema", response_model=Dict[str, Any])
async def get_database_schema(
    db: FloatChatDBManager = Depends(get_db_manager)
):
    """
    Get database schema information for the FloatChat tables.
    """
    try:
        table_info = db.get_table_info(['floats', 'cycles', 'profiles'])

        if not table_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No schema information found"
            )

        return {
            "schema": table_info,
            "description": "FloatChat database schema for ARGO float data",
            "tables": list(table_info.keys())
        }

    except Exception as e:
        logger.error(f"Error retrieving schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve database schema: {str(e)}"
        )

@app.get("/api/v1/stats", response_model=Dict[str, Any])
async def get_database_stats(
    db: FloatChatDBManager = Depends(get_db_manager)
):
    """
    Get database statistics and usage information.
    """
    try:
        stats = db.get_database_stats()

        return {
            "stats": stats,
            "timestamp": datetime.now().isoformat(),
            "description": "FloatChat database statistics"
        }

    except Exception as e:
        logger.error(f"Error retrieving stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve database statistics: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Simple health check endpoint for load balancers"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

def main():
    """
    Main function to run the FastAPI server.
    """
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info")
    workers = int(os.getenv("WORKERS", "1"))

    logger.info(f"Starting FloatChat API server on {host}:{port}")

    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        workers=workers,
        reload=False,  # Set to True for development
        access_log=True
    )

if __name__ == "__main__":
    main()

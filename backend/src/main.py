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
import requests
from groq import Groq
from openai import OpenAI
from mistralai import Mistral


from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from src.rag_core import FloatChatRAGCore, QueryResult
from src.db_manager import FloatChatDBManager, QueryExecutionResult
from src.chat_history_manager import ChatHistoryManager
from src.intent_service import IntentDetectionService, ResponseType, IntentResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables first
load_dotenv()

# --- LLM Configuration ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL")
OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")


# Configuration from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/floatchat")
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
MAX_QUERY_TIME = int(os.getenv("MAX_QUERY_TIME", "30"))

# Global instances (will be initialized in lifespan)
rag_core: Optional[FloatChatRAGCore] = None
db_manager: Optional[FloatChatDBManager] = None
chat_history_manager: Optional[ChatHistoryManager] = None
intent_service: Optional[IntentDetectionService] = None
llm_client: Any = None

def get_llm_client():
    """Initializes and returns the appropriate LLM client based on the environment configuration."""
    global llm_client
    if llm_client:
        return llm_client

    logger.info(f"Initializing LLM client for provider: {LLM_PROVIDER}")

    if LLM_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set")
        llm_client = Groq(api_key=GROQ_API_KEY)
    elif LLM_PROVIDER == "openrouter":
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not set")
        llm_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
    elif LLM_PROVIDER == "mistral":
        if not MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY is not set")
        llm_client = Mistral(api_key=MISTRAL_API_KEY)
    elif LLM_PROVIDER == "deepseek":
        # DeepSeek uses a requests-based approach, so we don't initialize a client here.
        # The API key will be checked in the handler.
        llm_client = "deepseek"
    else:
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

    logger.info(f"LLM client for {LLM_PROVIDER} initialized successfully.")
    return llm_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    global rag_core, db_manager, chat_history_manager, intent_service, llm_client

    logger.info("Starting FloatChat API server...")

    try:
        # Initialize LLM client
        llm_client = get_llm_client()

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
            llm_client=llm_client, # Pass the client
            llm_provider=LLM_PROVIDER
        )
        logger.info("RAG core initialized")

        # Initialize Intent Detection Service
        logger.info("Initializing Intent Detection Service...")
        intent_service = IntentDetectionService()
        logger.info("Intent Detection Service initialized")

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
    """Enhanced response model with intent information"""
    success: bool
    data: list
    sql_query: str
    row_count: int
    confidence_score: float
    execution_time: float
    reasoning: str
    response_type: str = Field(default="data_query", description="Type of response: conversational, data_query, visualization, map, etc.")
    visualization_type: Optional[str] = Field(default=None, description="Specific visualization type if applicable")
    error_message: Optional[str] = None
    context: Optional[list] = None

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

async def get_intent_service() -> IntentDetectionService:
    """Dependency for Intent Detection Service instance"""
    if intent_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Intent Detection Service not initialized"
        )
    return intent_service

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
async def process_query(
    request: QueryRequest,
    rag: FloatChatRAGCore = Depends(get_rag_core),
    db: FloatChatDBManager = Depends(get_db_manager),
    intent_service: IntentDetectionService = Depends(get_intent_service),
    chat_manager: ChatHistoryManager = Depends(get_chat_history_manager)
):
    """
    Dynamically process queries based on user intent
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Step 1: Get chat history for context
        recent_messages = []
        if request.session_id:
            try:
                recent_messages = chat_manager.get_recent_history(request.session_id, limit=10)
                logger.info(f"Retrieved {len(recent_messages)} messages for context")
            except Exception as e:
                logger.warning(f"Failed to retrieve chat history: {str(e)}")
        
        # Step 2: Analyze user intent with history context
        intent_result = intent_service.analyze_intent(request.query, chat_history=recent_messages)
        logger.info(f"Detected intent: {intent_result.response_type.value} (confidence: {intent_result.confidence:.2f})")
        
        # Step 3: Route based on intent
        if intent_result.response_type == ResponseType.CONVERSATIONAL:
            return await handle_conversational_query(request, intent_result, rag, chat_manager, start_time, recent_messages)
        
        elif intent_result.response_type == ResponseType.HELP:
            return await handle_help_query(request, chat_manager, start_time)
        
        elif intent_result.requires_data:
            return await handle_data_query(request, intent_result, rag, db, chat_manager, start_time, recent_messages)
        
        else:
            # Default to conversational for unclear intents
            return await handle_conversational_query(request, intent_result, rag, chat_manager, start_time, recent_messages)
            
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        total_execution_time = time.time() - start_time
        
        return QueryResponse(
            success=False,
            data=[],
            sql_query="",
            row_count=0,
            confidence_score=0.0,
            execution_time=total_execution_time,
            reasoning="Query processing failed due to internal error",
            error_message=f"Internal server error: {str(e)}"
        )


async def get_llm_response(client: Any, provider: str, messages: List[Dict[str, str]], **kwargs) -> str:
    """Gets a response from the configured LLM."""
    if provider == "groq":
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 8192),
            top_p=kwargs.get("top_p", 1),
            stream=False,
        )
        return completion.choices[0].message.content
    elif provider == "openrouter":
        extra_headers = {}
        if OPENROUTER_SITE_URL:
            extra_headers["HTTP-Referer"] = OPENROUTER_SITE_URL
        if OPENROUTER_SITE_NAME:
            extra_headers["X-Title"] = OPENROUTER_SITE_NAME

        completion = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            extra_headers=extra_headers,
        )
        return completion.choices[0].message.content
    elif provider == "mistral":
        completion = client.chat.completions.create(
            model=MISTRAL_MODEL,
            messages=messages,
        )
        return completion.choices[0].message.content
    elif provider == "deepseek":
        if not DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY is not set")
        
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 300),
            "top_p": kwargs.get("top_p", 0.9)
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        llm_endpoint = "https://api.deepseek.com/v1/chat/completions"
        
        response = requests.post(llm_endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


async def handle_conversational_query(request: QueryRequest, intent_result: IntentResult, rag: FloatChatRAGCore, chat_manager: ChatHistoryManager, start_time: float, recent_messages: List[Dict[str, Any]]):
    """Handle conversational queries using the configured LLM"""
    
    conversation_context = ""
    if recent_messages:
        try:
            conversation_context_lines = []
            for msg in recent_messages[-5:]: 
                if msg['role'] == 'user':
                    conversation_context_lines.append(f"User: {msg['content']}")
                elif msg['role'] == 'assistant':
                    conversation_context_lines.append(f"Assistant: {msg['content']}")
            conversation_context = "\n".join(conversation_context_lines)
        except Exception as e:
            logger.warning(f"Failed to format conversation context: {str(e)}")
    
    system_prompt = """You are a friendly and knowledgeable oceanographic data assistant. You help users explore ARGO float data and ocean science topics through natural conversation. 

Key behaviors:
1. Be conversational, warm, and engaging
2. Provide helpful information about ocean data and ARGO floats
3. Always encourage users to explore more by asking relevant follow-up questions
4. Keep responses concise but informative
5. If users ask about data capabilities, guide them toward specific queries
6. Use phrases like "Would you like to...", "I can help you with...", "Let me know if you'd like to explore..."

Remember: You don't need to fetch data from databases for conversational queries - just provide helpful, engaging responses that encourage further exploration."""

    user_prompt = f"""{conversation_context}

User: {request.query}

Please provide a helpful, conversational response that encourages the user to explore more ocean data topics."""

    try:
        client = get_llm_client()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        conversational_response = await get_llm_response(client, LLM_PROVIDER, messages)
        logger.info(f"LLM generated conversational response: {conversational_response[:100]}...")

    except Exception as e:
        logger.error(f"Error invoking LLM for conversational query: {str(e)}")
        conversational_response = "I'd love to help you explore ocean data! What would you like to discover about our ARGO float measurements?"

    total_execution_time = time.time() - start_time
    
    response = QueryResponse(
        success=True,
        data=[{"message": conversational_response, "type": "conversational"}],
        sql_query="",
        row_count=0,
        confidence_score=intent_result.confidence,
        execution_time=total_execution_time,
        reasoning=f"Conversational response powered by {LLM_PROVIDER} - {intent_result.reasoning}",
        response_type="conversational"
    )

    if request.session_id:
        chat_manager.add_message(request.session_id, "user", request.query)
        chat_manager.add_message(
            request.session_id,
            "assistant",
            conversational_response,
            full_response=response.dict()
        )
        chat_manager.cleanup_old_messages(request.session_id)
        
    return response

async def handle_help_query(request: QueryRequest, chat_manager: ChatHistoryManager, start_time: float):
    """Handle help and capability queries using the configured LLM"""
    
    system_prompt = """You are a helpful oceanographic data assistant. When users ask for help or what you can do, provide a warm, conversational overview of your capabilities focused on ARGO float data exploration.

Key points to cover:
- Query oceanographic data from ARGO floats worldwide
- Generate charts and visualizations of temperature, salinity, and other parameters
- Show float locations and trajectories on interactive maps
- Analyze trends over time and compare different regions
- Search by geographic locations (e.g., "near Japan", "Indian Ocean")
- Provide data summaries and statistical insights

Keep responses conversational and end with an engaging question to encourage exploration."""

    user_prompt = f"User: {request.query}\n\nPlease provide a helpful, conversational response about what I can help with regarding ARGO float data exploration."

    try:
        client = get_llm_client()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        help_response = await get_llm_response(client, LLM_PROVIDER, messages)

    except Exception as e:
        logger.error(f"Error invoking LLM for help query: {str(e)}")
        help_response = "I can help you explore ARGO float data including temperature, salinity, and location information. What would you like to discover about our ocean measurements?"

    total_execution_time = time.time() - start_time
    
    response = QueryResponse(
        success=True,
        data=[{"message": help_response, "type": "help"}],
        sql_query="",
        row_count=0,
        confidence_score=0.9,
        execution_time=total_execution_time,
        reasoning=f"Help response powered by {LLM_PROVIDER}",
        response_type="help"
    )

    if request.session_id:
        chat_manager.add_message(request.session_id, "user", request.query)
        chat_manager.add_message(
            request.session_id,
            "assistant",
            help_response,
            full_response=response.dict()
        )
        chat_manager.cleanup_old_messages(request.session_id)

    return response

async def handle_data_query(request: QueryRequest, intent_result: IntentResult, rag: FloatChatRAGCore, db: FloatChatDBManager, chat_manager: ChatHistoryManager, start_time: float, recent_messages: List[Dict[str, Any]]):
    """Handle queries that require data processing - your existing logic"""
    
    conversation_context = None
    if recent_messages:
        try:
            conversation_context_lines = []
            for msg in recent_messages:
                if msg['role'] == 'user':
                    conversation_context_lines.append(f"USER: {msg['content']}")
                elif msg['role'] == 'assistant':
                    assistant_msg = f"ASSISTANT: {msg['content']}"
                    if msg.get('full_response') and msg['full_response'].get('sql_query'):
                        assistant_msg += f"\nSQL GENERATED: {msg['full_response']['sql_query']}"
                    conversation_context_lines.append(assistant_msg)
            
            conversation_context = "\n".join(conversation_context_lines)
            logger.info(f"Using enhanced conversation context with {len(recent_messages)} messages")
            
        except Exception as e:
            logger.warning(f"Failed to format conversation context: {str(e)}")
    
    query_for_embedding = request.query
    if recent_messages:
        user_messages = [msg['content'] for msg in recent_messages if msg['role'] == 'user']
        if user_messages:
            query_for_embedding = user_messages[-1] + " " + request.query

    rag_result: QueryResult = await rag.process_query(query_for_embedding, conversation_context)
    
    if not rag_result.sql_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to generate SQL query from natural language input"
        )
    
    db_result: QueryExecutionResult = db.execute_query(rag_result.sql_query)
    
    response_type = intent_result.response_type.value
    visualization_type = intent_result.visualization_type
    
    limited_data = db_result.data[:request.max_results] if db_result.data else []
    total_execution_time = time.time() - start_time
    
    response = QueryResponse(
        success=db_result.success,
        data=limited_data,
        sql_query=rag_result.sql_query,
        row_count=len(limited_data),
        confidence_score=rag_result.confidence_score,
        execution_time=total_execution_time,
        reasoning=rag_result.reasoning,
        response_type=response_type,
        visualization_type=visualization_type,
        error_message=db_result.error_message if not db_result.success else None
    )

    if request.session_id:
        chat_manager.add_message(request.session_id, "user", request.query)
        chat_manager.add_message(
            request.session_id,
            "assistant",
            rag_result.reasoning,
            full_response=response.dict()
        )
        chat_manager.cleanup_old_messages(request.session_id)

    return response

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
    port = int(os.getenv("PORT", "8001")) # Changed port to 8001 to avoid conflict with frontend
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
        reload=True,
        access_log=True
    )

if __name__ == "__main__":
    main()
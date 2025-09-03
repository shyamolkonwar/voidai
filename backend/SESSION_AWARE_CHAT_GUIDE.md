# Session-Aware Chat Implementation Guide

## Overview

This implementation adds smart context awareness to the FloatChat application, enabling each chat session to "remember" prior messages and support deeper, multi-turn exploration. The system uses a lightweight memory store on top of the existing Next.js + Python backend.

## Key Features Implemented

### ✅ Backend Changes
1. **Database Schema**: Created `chat_history` table with session-based storage
2. **Chat History Manager**: New module for session management and message persistence
3. **Session API Endpoints**: 
   - `POST /api/v1/sessions` - Create new chat session
   - `GET /api/v1/sessions/{session_id}/history` - Get session history
4. **RAG Integration**: Enhanced prompt engineering with conversation context
5. **Token Management**: Automatic token counting and history optimization

### ✅ Frontend Changes
1. **Dynamic Routing**: New `/chat/[session_id]` route for session-based URLs
2. **Session Management**: `useSession` hook for session creation and management
3. **API Integration**: Updated `useChat` hook to include session IDs in requests
4. **History Loading**: Session history loading on page navigation

### ✅ Database Changes
- New `chat_history` table with session-based storage
- Automatic cleanup and optimization of old messages
- Token counting and metadata storage

## Setup Instructions

### 1. Database Setup
```bash
# Apply the database migration
cd backend/supabase
supabase migration up
```

### 2. Backend Setup
```bash
cd backend
pip install -r config/requirements.txt
# Install additional dependency for token counting
pip install tiktoken

# Start the backend server
python -m src.main
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Testing the Implementation

### Option 1: Automated Test
```bash
cd backend
python test_session_chat.py
```

### Option 2: Manual Testing

1. **Start the backend server** on http://127.0.0.1:8001
2. **Start the frontend** on http://localhost:3000
3. **Test session flow**:
   - Visit http://localhost:3000/ - creates a new session automatically
   - Send a query like "Show me ocean temperature data"
   - Notice the URL changes to `/chat/{session_id}`
   - Send follow-up queries like "Now show salinity data"
   - Reload the page - conversation history is preserved
   - Open multiple tabs with different session IDs

### Option 3: API Testing with curl

```bash
# Create a new session
curl -X POST http://127.0.0.1:8001/api/v1/sessions

# Send query with session context
curl -X POST http://127.0.0.1:8001/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me temperature data",
    "session_id": "your-session-id-here",
    "max_results": 5
  }'

# Get session history
curl http://127.0.0.1:8001/api/v1/sessions/your-session-id-here/history
```

## Session Management Features

### URL-Based Sessions
- Each chat gets a unique URL: `/chat/123e4567-e89b-12d3-a456-426614174000`
- Session IDs are stored in browser local storage for persistence
- Users can bookmark or share specific conversations

### Context Awareness
- Conversation history is included in LLM prompts
- Follow-up queries maintain context from previous messages
- Multi-turn exploration without repeating information

### Token Optimization
- Automatic token counting and message truncation
- Conversation history summarization when token limits are exceeded
- Configurable limits: 4000 tokens per session, 1000 tokens per message

### Database Persistence
- Messages stored in PostgreSQL with session-based indexing
- Automatic cleanup of old messages (keeps last 20 messages)
- Metadata storage including token counts and timestamps

## File Structure Changes

### Backend
```
backend/
├── src/
│   ├── chat_history_manager.py    # New session management module
│   ├── main.py                    # Updated with session endpoints
│   └── rag_core.py                # Enhanced with context awareness
├── supabase/
│   └── migrations/
│       └── 20250103000000_create_chat_history.sql
└── test_session_chat.py           # Test script
```

### Frontend
```
frontend/
├── app/
│   ├── chat/
│   │   └── [session_id]/
│   │       └── page.tsx           # Dynamic session route
│   └── page.tsx                   # Updated with session redirects
├── hooks/
│   ├── useChat.ts                 # Updated with session support
│   └── useSession.ts              # New session management hook
└── types/
    └── api.ts                     # Updated QueryRequest interface
```

## Configuration

### Environment Variables
```bash
# Optional: Configure token limits
export MAX_SESSION_TOKENS=4000
export MAX_MESSAGE_TOKENS=1000
export MAX_SESSION_MESSAGES=20
```

### Database Configuration
The system uses the existing PostgreSQL connection configured in `DATABASE_URL`.

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify PostgreSQL is running
   - Check `DATABASE_URL` environment variable

2. **Session Not Persisting**
   - Check browser local storage
   - Verify backend session endpoints are working

3. **Token Counting Errors**
   - Ensure `tiktoken` is installed: `pip install tiktoken`

4. **CORS Issues**
   - Backend is configured with CORS enabled for all origins
   - For production, update CORS settings in `backend/src/main.py`

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export LOG_LEVEL=debug
```

## Production Considerations

1. **Database Indexing**: Ensure proper indexes on `chat_history` table
2. **Session Cleanup**: Implement periodic cleanup of old sessions
3. **Rate Limiting**: Add rate limiting for session creation
4. **Authentication**: Add user authentication to session management
5. **Backup**: Regular backups of chat history data

## Performance Notes

- Each message adds ~1-2ms overhead for token counting
- Session history retrieval is optimized with database indexes
- Conversation optimization runs asynchronously to avoid blocking
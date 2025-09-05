# VOID: Natural Language Query Interface for Oceanographic Data

## Overview  
VOID is an AI-powered full-stack application that enables natural-language querying of oceanographic float data. Users can ask questions—such as "Show me temperature trends near Mumbai"—and VOID translates them into SQL queries, executes them against a Supabase (PostgreSQL) database, and returns structured results with dynamic visualizations (maps, charts, tables) and conversational interactions.

***

## Key Features  
- **ETL Pipeline**: Ingest ARGO NetCDF files, transform into star schema, load into Supabase  
- **Retrieval-Augmented Generation**:  
  - Embedding-based context retrieval with ChromaDB  
  - Prompt engineering with schema, few-shot examples, safety constraints  
- **LLM Integration**: Plug-and-play with any LLM via HTTP API  
- **Database Manager**: Secure SELECT-only enforcement, SQL injection prevention  
- **Dynamic Intent Handling**: Detects conversational, data, visualization, map, summary, comparison, and help intents  
- **Geographic Intelligence**: Converts location names (e.g., "Mumbai") into proximity SQL conditions using Haversine formula  
- **API Layer**: Next.js frontend with FastAPI backend endpoints  
- **Context Awareness**: Session-based chat history stored in Supabase for multi-turn conversations  
- **Real-time Visualizations**: Interactive charts, maps, and data tables  
- **Session Management**: Full chat history with conversation persistence  

***

## Technology Stack  
- **Frontend**: Next.js 14 (React), TypeScript, Tailwind CSS, React Map GL, Chart.js  
- **Backend**: Python 3.11+, FastAPI, Uvicorn  
- **Database**: Supabase (PostgreSQL)  
- **Vector Store**: ChromaDB  
- **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`)  
- **LLM**: Any HTTP-accessible LLM (e.g., OpenAI, Ollama)  
- **ETL**: xarray, netCDF4, pandas, numpy  
- **Intent Detection**: Custom rule-based service  
- **Geocoding**: Internal lookup + OpenStreetMap Nominatim fallback  
- **Testing**: pytest, pytest-asyncio, httpx  

***

## Complete Repository Structure

```
VOID_1/
├── .gitignore
├── README.md
├── backend/
│   ├── SESSION_AWARE_CHAT_GUIDE.md
│   ├── app.py                          # Streamlit app (alternative frontend)
│   ├── cleanup_duplicates.py          # Data cleaning utilities
│   ├── run_etl.py                     # ETL pipeline runner
│   ├── run_server.py                  # FastAPI server runner
│   ├── setup_database.py              # Database schema setup
│   ├── start_server.sh                # Server startup script
│   ├── config/
│   │   └── requirements.txt           # Python dependencies
│   ├── data/                          # ARGO NetCDF data storage
│   ├── src/                           # Core backend modules
│   │   ├── __init__.py
│   │   ├── argo_data_reader.py        # ARGO data file reader
│   │   ├── chat_history_manager.py    # Session-based chat management
│   │   ├── db_manager.py              # Database connection & query execution
│   │   ├── etl_pipeline.py            # ETL pipeline implementation
│   │   ├── intent_service.py          # Intent detection & classification
│   │   ├── main.py                    # FastAPI application & endpoints
│   │   └── rag_core.py                # RAG system & prompt engineering
│   ├── supabase/                      # Supabase configuration
│   │   ├── config.toml
│   │   └── migrations/
│   │       ├── 20250103000000_create_chat_history.sql
│   │       └── 20250104000000_add_full_response_column.sql
│   └── tests/                         # Backend test suite
│       ├── test_context_awareness.py
│       ├── test_full_response_feature.py
│       └── test_session_chat.py
└── frontend/                          # Next.js frontend
    ├── .gitignore
    ├── next.config.js                 # Next.js configuration
    ├── package.json                   # Frontend dependencies
    ├── package-lock.json
    ├── tsconfig.json                  # TypeScript configuration
    ├── tailwind.config.js             # Tailwind CSS configuration
    ├── postcss.config.js              # PostCSS configuration
    ├── app/                           # Next.js App Router
    │   ├── layout.tsx                 # Root layout component
    │   ├── page.tsx                   # Home page
    │   ├── about/                     # About page
    │   │   └── page.tsx
    │   ├── api/                       # Frontend API routes (proxy to backend)
    │   │   └── chat/
    │   │       ├── route.ts           # Main chat API endpoint
    │   │       └── sessions/
    │   │           └── route.ts       # Session management endpoints
    │   └── chat/                      # Chat interface page
    │       └── page.tsx
    ├── components/                    # React components
    │   ├── Footer.tsx
    │   ├── GlassCard.tsx
    │   ├── Hero.tsx
    │   ├── LenisProvider.tsx
    │   ├── NavConditional.tsx
    │   ├── Navbar.tsx
    │   └── chat/                      # Chat-specific components
    │       ├── ChartCard.tsx          # Data visualization charts
    │       ├── ChatBox.tsx            # Main chat container
    │       ├── ChatInput.tsx          # Message input component
    │       ├── ChatShell.tsx          # Chat interface shell
    │       ├── DataTableCard.tsx      # Tabular data display
    │       ├── Loader.tsx             # Loading indicators
    │       ├── MapCard.tsx            # Interactive maps
    │       ├── MessageList.tsx        # Chat message display
    │       └── Sidebar.tsx            # Chat session sidebar
    ├── styles/                        # Global styles
    │   ├── globals.css
    │   └── scrollbar.css
    └── types/                         # TypeScript type definitions
        ├── api.ts                     # API request/response types
        └── react-map-gl.d.ts
```

***

## Backend API Endpoints

### Core Query Endpoints

#### 1. Process Natural Language Query
- **Endpoint**: `POST /api/v1/query`
- **Description**: Process natural language queries with intent detection and context awareness
- **Request Body**:
```json
{
  "query": "Show me temperature trends near Mumbai",
  "session_id": "uuid-string",
  "include_context": true,
  "max_results": 100
}
```
- **Response**:
```json
{
  "success": true,
  "data": [...],
  "sql_query": "SELECT ...",
  "row_count": 50,
  "confidence_score": 0.95,
  "execution_time": 2.5,
  "reasoning": "Generated query for temperature trends...",
  "response_type": "data_query",
  "visualization_type": "line_chart",
  "context": [...]
}
```

### Session Management Endpoints

#### 2. Create New Session
- **Endpoint**: `POST /api/v1/sessions`
- **Description**: Create a new chat session for conversation tracking
- **Response**:
```json
{
  "session_id": "uuid-string",
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### 3. Get All Sessions
- **Endpoint**: `GET /api/v1/sessions`
- **Description**: Retrieve all chat sessions with metadata
- **Response**:
```json
{
  "sessions": [
    {
      "session_id": "uuid-string",
      "created_at": "2024-01-01T12:00:00Z",
      "last_activity": "2024-01-01T12:30:00Z",
      "message_count": 15
    }
  ]
}
```

#### 4. Get Session History
- **Endpoint**: `GET /api/v1/sessions/{session_id}/history`
- **Description**: Get complete chat history for a specific session
- **Response**:
```json
{
  "session_id": "uuid-string",
  "messages": [
    {
      "role": "user",
      "content": "Show me temperature data",
      "created_at": "2024-01-01T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Here are the temperature measurements...",
      "created_at": "2024-01-01T12:00:30Z",
      "full_response": {...}
    }
  ],
  "message_count": 10
}
```

### Health & Status Endpoints

#### 5. Service Health Check
- **Endpoint**: `GET /api/v1/status`
- **Description**: Check service health and component status
- **Response**:
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "database_connected": true,
  "rag_initialized": true
}
```

#### 6. Root Endpoint
- **Endpoint**: `GET /`
- **Description**: Basic API information and documentation link
- **Response**:
```json
{
  "message": "FloatChat API",
  "description": "Natural Language to SQL API for ARGO Float Data",
  "version": "1.0.0",
  "documentation": "/docs"
}
```

### Intent Detection Types
The system automatically detects and handles these query types:
- **data_query**: Data retrieval queries (SQL generation)
- **visualization**: Chart and graph requests
- **map**: Geographic visualization requests
- **summary**: Data summarization requests
- **comparison**: Comparative analysis requests
- **conversational**: General chat responses
- **help**: System capability queries

***

## Frontend API Routes (Proxy to Backend)

The frontend uses Next.js API routes as a proxy to the backend for CORS handling and environment management:

### 1. Chat Query Proxy
- **File**: `/frontend/app/api/chat/route.ts`
- **Frontend Endpoint**: `POST /api/chat`
- **Proxies to**: `POST /api/v1/query`

### 2. Session Management Proxy
- **File**: `/frontend/app/api/chat/sessions/route.ts`
- **Frontend Endpoints**:
  - `POST /api/chat/sessions` → Creates new session
  - `GET /api/chat/sessions` → Lists all sessions

### Frontend-Backend Connection Flow

1. **Frontend Request**: User submits query in chat interface
2. **Frontend API Route**: Next.js API route receives request
3. **Proxy Forwarding**: Request forwarded to FastAPI backend
4. **Backend Processing**: Intent detection → SQL generation → Data retrieval
5. **Response Return**: Results returned through same proxy chain
6. **Frontend Rendering**: Dynamic visualization based on response_type

***

## Database Schema

### Core Tables

#### 1. floats
- `float_id` (String, Primary Key)
- `wmo_id` (String)
- `project_name` (String)
- `pi_name` (String)
- `platform_type` (String)
- `deployment_date` (DateTime)
- `last_update` (DateTime)

#### 2. cycles
- `cycle_id` (String, Primary Key)
- `float_id` (String, Foreign Key)
- `cycle_number` (Integer)
- `profile_date` (DateTime)
- `latitude` (Float)
- `longitude` (Float)
- `profile_type` (String)

#### 3. profiles
- `profile_id` (String, Primary Key)
- `cycle_id` (String, Foreign Key)
- `pressure` (Float)
- `temperature` (Float)
- `salinity` (Float)
- `depth` (Float)
- `quality_flag` (Integer)

#### 4. chat_history
- `session_id` (String, Primary Key)
- `turn_index` (Integer, Primary Key)
- `role` (String)
- `message` (Text)
- `created_at` (DateTime)
- `metadata` (JSON)

## Smart Context Awareness System

VOID features a sophisticated session-aware chat system that enables multi-turn conversations with persistent memory, allowing users to have deeper, contextually-aware interactions with oceanographic data.

### Core Features

#### 🔍 **Session-Based Memory**
- **Persistent Conversations**: Each chat session maintains complete message history in PostgreSQL
- **URL-Based Sessions**: Unique session IDs create shareable conversation URLs (`/chat/{session_id}`)
- **Automatic Session Creation**: New sessions created seamlessly when users start chatting
- **Cross-Tab Persistence**: Sessions work across browser tabs and survive page refreshes

#### 🧠 **Context-Aware Processing**
- **Conversation History Integration**: Previous messages automatically included in LLM prompts
- **Follow-up Query Support**: "Now show me salinity data" works without repeating location context
- **Multi-turn Exploration**: Users can drill down into data with natural follow-up questions
- **Smart Context Truncation**: Automatic token management prevents context overflow

#### 🛡️ **Token Optimization**
- **Dynamic Token Counting**: Real-time token calculation using `tiktoken`
- **Intelligent Truncation**: Automatically trims old messages when approaching limits
- **Configurable Limits**: 
  - 4,000 tokens per session maximum
  - 1,000 tokens per message maximum
  - 20 messages retained per session
- **Conversation Summarization**: Long conversations summarized to maintain context

### Technical Implementation

#### Backend Architecture
- **ChatHistoryManager**: Dedicated module for session management and message persistence
- **Enhanced RAG Core**: Modified to include conversation context in prompt engineering
- **Session API Endpoints**: RESTful endpoints for session lifecycle management
- **Database Integration**: PostgreSQL-based storage with optimized indexing

#### Frontend Components
- **Dynamic Routing**: Next.js App Router handles `/chat/[session_id]` routes
- **SessionManager Hook**: Frontend utility for session creation and validation
- **ChatShell Component**: Main chat interface with session-aware message handling
- **State Synchronization**: Real-time sync between frontend state and backend sessions

### API Endpoints

#### Session Management
```bash
# Create new session
POST /api/v1/sessions
Response: {"session_id": "uuid-string", "created_at": "2024-01-01T12:00:00Z"}

# Get session history
GET /api/v1/sessions/{session_id}/history
Response: {"session_id": "uuid", "messages": [...], "message_count": 10}

# List all sessions
GET /api/v1/sessions
Response: {"sessions": [{"session_id": "uuid", "created_at": "...", "message_count": 5}]}
```

#### Enhanced Query Processing
```bash
# Context-aware query with session ID
POST /api/v1/query
{
  "query": "Now show me salinity data for the same region",
  "session_id": "existing-session-uuid",
  "include_context": true
}
```

### Usage Examples

#### Multi-turn Conversation Flow
```
User: "Show me temperature data near Mumbai"
Assistant: [Shows temperature data with map visualization]

User: "What about salinity in that same area?"
Assistant: [Automatically uses Mumbai context, shows salinity data]

User: "Plot this over time"
Assistant: [Creates time-series chart using previous query context]
```

#### Session Sharing
```bash
# Share conversation via URL
https://void.example.com/chat/123e4567-e89b-12d3-a456-426614174000

# Bookmark specific data exploration session
# Session persists across browser restarts
```

### Setup & Configuration

#### Environment Variables
```bash
# Optional token limits
export MAX_SESSION_TOKENS=4000
export MAX_MESSAGE_TOKENS=1000
export MAX_SESSION_MESSAGES=20
```

#### Database Setup
```bash
# Apply session table migration
cd backend/supabase
supabase migration up

# Install additional dependency
pip install tiktoken
```

### Performance Characteristics

- **Message Overhead**: ~1-2ms per message for token counting
- **Session Retrieval**: <50ms for 20-message session history
- **Memory Usage**: ~2KB per message (including metadata)
- **Scalability**: PostgreSQL indexing handles thousands of concurrent sessions

### Testing & Validation

#### Automated Testing
```bash
# Run session-aware chat tests
cd backend
python test_session_chat.py

# Test context awareness
pytest tests/test_context_awareness.py -v
```

#### Manual Testing
1. Start backend: `python -m src.main`
2. Start frontend: `npm run dev`
3. Test conversation flow at `http://localhost:3000`
4. Verify session persistence across page reloads
5. Test multi-turn queries with geographic context

### Security & Privacy

- **Session Isolation**: Each session completely isolated from others
- **Data Retention**: Automatic cleanup of old messages (configurable)
- **No Cross-session Access**: Sessions cannot access other session data
- **URL Security**: Session IDs are UUID v4, cryptographically secure
- **Privacy Mode**: Sessions can be configured for temporary use

### Troubleshooting

#### Common Issues
- **Session Not Found**: Ensure session ID is valid and not expired
- **Token Limit Exceeded**: Check `MAX_SESSION_TOKENS` configuration
- **Context Loss**: Verify conversation history is being sent in requests
- **CORS Issues**: Ensure frontend `BACKEND_URL` matches backend origin

#### Debug Commands
```bash
# Check session count
SELECT COUNT(*) FROM chat_history WHERE session_id = 'your-session-id';

# View recent session messages
SELECT * FROM chat_history 
WHERE session_id = 'your-session-id' 
ORDER BY created_at DESC LIMIT 5;
```

***

## Geographic Intelligence Enhancements

### Recent Improvements to Location-Based Queries

The geographic lookup service has been significantly enhanced to provide more accurate and comprehensive location-based queries:

#### PostgreSQL Compatibility
- **Full PostgreSQL Support**: Updated all geographic queries to use PostgreSQL-compatible syntax
- **Table Reference Updates**: Changed from generic aliases to explicit table names (e.g., `cycles.latitude` instead of `c.latitude`)
- **Haversine Formula**: Implemented PostgreSQL-optimized Haversine distance calculations for precise geographic proximity queries

#### Enhanced Query Radius
- **Expanded Coverage**: Increased default search radius from 200km to 500km for broader geographic coverage
- **Configurable Distance**: Flexible radius adjustment based on query context and user requirements
- **Global Coordinate Validation**: Validates coordinate ranges across all ARGO deployment areas (-90 to 90 latitude, -180 to 180 longitude)

#### Improved Location Context
- **Bounding Box Calculations**: Added automatic bounding box generation for debugging and query optimization
- **Quality Flag Integration**: Filters results by data quality flags to ensure reliable measurements
- **Multi-parameter Support**: Returns temperature, salinity, depth, and distance calculations in geographic queries

#### Query Examples
```sql
-- Mumbai temperature data within 500km radius
SELECT cycles.cycle_id, cycles.latitude, cycles.longitude, 
       profiles.temperature, profiles.salinity, profiles.depth,
       (6371 * acos(
           cos(radians(19.0760)) * cos(radians(cycles.latitude)) * 
           cos(radians(cycles.longitude) - radians(72.8777)) + 
           sin(radians(19.0760)) * sin(radians(cycles.latitude))
       )) AS distance_km
FROM cycles 
JOIN profiles ON cycles.cycle_id = profiles.cycle_id
WHERE (6371 * acos(...)) <= 500
  AND profiles.quality_flag = 1
ORDER BY distance_km ASC
LIMIT 20;
```

#### Testing & Validation
- **Coordinate Range Verification**: Automated testing confirms global coverage with 28,815+ cycles
- **Sample Results**: Mumbai query returns 20 temperature measurements within 500km radius
- **Distance Accuracy**: Precise distance calculations using spherical Earth model
- **Fallback Mechanisms**: Graceful handling when no geographic data matches criteria

***

## Complete Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (via Supabase)
- Git

### 1. Clone and Setup

```bash
git clone <https://github.com/shyamolkonwar/voidai.git>
cd VOID_1
```

### 2. Backend Setup

#### Environment Configuration
Create `/backend/.env` file:
```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/floatchat

# Vector Database
CHROMA_HOST=localhost
CHROMA_PORT=8000

# LLM Configuration
LLM_ENDPOINT=http://localhost:11434/api/generate
# For OpenAI: LLM_ENDPOINT=https://api.openai.com/v1/chat/completions

# API Configuration
MAX_QUERY_TIME=30
```

#### Install Dependencies
```bash
cd backend
pip install -r config/requirements.txt
```

#### Database Setup
```bash
# Option 1: Using setup script
python setup_database.py

# Option 2: Manual setup with Supabase
# 1. Create Supabase project
# 2. Update DATABASE_URL in .env
# 3. Run migrations:
psql $DATABASE_URL -f supabase/migrations/20250103000000_create_chat_history.sql
psql $DATABASE_URL -f supabase/migrations/20250104000000_add_full_response_column.sql
```

#### Start Backend Services
```bash
# Option 1: Using run script
python run_server.py

# Option 2: Direct FastAPI
uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

# Option 3: Using shell script
./start_server.sh
```

### 3. Frontend Setup

#### Environment Configuration
Create `/frontend/.env.local` file:
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8001
BACKEND_URL=http://localhost:8001
```

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Start Frontend Development Server
```bash
npm run dev
# Frontend will be available at http://localhost:3000
```

### 4. ETL Pipeline Setup (Optional)

#### Prepare ARGO Data
```bash
# Place NetCDF files in backend/data/
# Files should follow ARGO naming conventions
```

#### Run ETL Pipeline
```bash
cd backend
python run_etl.py
```

### 5. Testing Setup

#### Backend Tests
```bash
cd backend
pytest tests/ -v
```

#### Frontend Tests
```bash
cd frontend
npm run test
```

### 6. Production Deployment

#### Backend Production
```bash
cd backend
# Using Gunicorn for production
pip install gunicorn
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

#### Frontend Production
```bash
cd frontend
npm run build
npm start
```

***

## Usage Examples

### Starting a New Chat
1. Open frontend at `http://localhost:3000`
2. Click "New Chat" to create session
3. Start asking questions:
   - "Show me temperature data from float 5904471"
   - "Plot salinity trends over time"
   - "Map float locations near Japan"
   - "Compare temperature between Atlantic and Pacific"

### API Testing with curl

```bash
# Create session
curl -X POST http://localhost:8001/api/v1/sessions

# Send query
curl -X POST http://localhost:8001/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show temperature data", "session_id": "your-session-id"}'

# Get session history
curl http://localhost:8001/api/v1/sessions/your-session-id/history
```

***

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure DATABASE_URL is correctly formatted
2. **CORS Issues**: Check frontend .env.local has correct BACKEND_URL
3. **LLM Connection**: Verify LLM_ENDPOINT is accessible
4. **Port Conflicts**: Ensure ports 3000 (frontend) and 8001 (backend) are available

### Debug Mode
```bash
# Backend debug
python -m src.main --debug

# Frontend debug
npm run dev -- --verbose
```
***

VOID empowers researchers to explore oceanographic float data using natural language, dynamic visualizations, and context-aware AI—bringing deep exploratory analysis within reach.
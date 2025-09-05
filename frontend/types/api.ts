// API types for FloatChat backend communication

export interface QueryRequest {
  query: string;
  session_id?: string;
  include_context?: boolean;
  max_results?: number;
}

export interface QueryResponse {
  success: boolean;
  data: any[];
  sql_query: string;
  row_count: number;
  confidence_score: number;
  execution_time: number;
  reasoning: string;
  response_type: string;
  visualization_type?: string;
  error_message?: string;
  context?: any[];
}

export interface SessionCreateResponse {
  session_id: string;
  created_at: string;
}

export interface SessionHistoryResponse {
  session_id: string;
  messages: ChatMessage[];
  message_count: number;
}

export interface SessionListResponse {
  sessions: SessionInfo[];
}

export interface SessionInfo {
  id: string;
  title: string;
  created_at: string;
  message_count: number;
  last_message_at?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  full_response?: QueryResponse;
}

export interface StatusResponse {
  status: string;
  timestamp: string;
  version: string;
  database_connected: boolean;
  rag_initialized: boolean;
}

export interface ApiError {
  error: string;
  message: string;
  statusCode: number;
}
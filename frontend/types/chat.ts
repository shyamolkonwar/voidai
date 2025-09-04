export interface Chat {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  response?: ApiResponse;
  isLoading?: boolean;
}

export interface ApiResponse {
  type: "map" | "table" | "text";
  data?: any;
  summary: string;
  sql_query?: string;
  row_count?: number;
  confidence_score?: number;
  execution_time?: number;
  reasoning?: string;
  success?: boolean;
  error_message?: string;
  context?: any[];
  full_response?: any;
}
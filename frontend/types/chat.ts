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
}

export interface ApiResponse {
  type: "map" | "table" | "text";
  data?: any;
  summary: string;
}
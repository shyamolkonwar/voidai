export interface QueryRequest {
  query: string;
  session_id?: string;
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
}

export interface MapData {
  latitudes: number[];
  longitudes: number[];
  labels?: string[];
}

export interface TableData {
  [key: string]: any;
}
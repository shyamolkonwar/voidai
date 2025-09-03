export interface QueryRequest {
  query: string;
  session_id?: string;
}

export interface ApiResponse {
  type: "map" | "table" | "text";
  data?: any;
  summary: string;
}

export interface MapData {
  latitudes: number[];
  longitudes: number[];
  labels?: string[];
}

export interface TableData {
  [key: string]: any;
}
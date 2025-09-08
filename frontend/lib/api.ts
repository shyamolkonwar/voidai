import { QueryRequest, QueryResponse, SessionCreateResponse, SessionListResponse, SessionHistoryResponse, ApiError } from '../types/api';

const API_BASE = '/api';

export class ApiClient {
  static async sendQuery(request: QueryRequest): Promise<QueryResponse> {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.message || 'Failed to send query');
    }

    return response.json();
  }

  static async createSession(): Promise<SessionCreateResponse> {
    const response = await fetch(`${API_BASE}/chat/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.message || 'Failed to create session');
    }

    return response.json();
  }

  static async getSessions(): Promise<SessionListResponse> {
    const response = await fetch(`${API_BASE}/chat/sessions`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.message || 'Failed to fetch sessions');
    }

    return response.json();
  }

  static async getSessionHistory(sessionId: string): Promise<SessionHistoryResponse> {
    const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}/history`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.message || 'Failed to fetch session history');
    }

    return response.json();
  }

  static async checkBackendHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${process.env.BACKEND_URL || 'http://localhost:8001'}/health`, {
        method: 'GET',
      });
      return response.ok;
    } catch (error) {
      console.error('Backend health check failed:', error);
      return false;
    }
  }
}
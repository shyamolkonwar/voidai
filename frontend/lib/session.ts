import { ApiClient } from './api';
import { sessionStorage } from './storage';

export class SessionManager {
  private static SESSION_STORAGE_KEY = 'float_chat_session_id';

  static async getOrCreateSession(): Promise<string> {
    // Try to get existing session from storage
    const existingSessionId = sessionStorage.getItem(this.SESSION_STORAGE_KEY);
    
    if (existingSessionId) {
      // Verify the session still exists on backend
      try {
        await ApiClient.getSessionHistory(existingSessionId);
        return existingSessionId;
      } catch (error) {
        console.warn('Existing session not found on backend, creating new one:', error);
        sessionStorage.removeItem(this.SESSION_STORAGE_KEY);
      }
    }

    // Create new session
    try {
      const response = await ApiClient.createSession();
      sessionStorage.setItem(this.SESSION_STORAGE_KEY, response.session_id);
      return response.session_id;
    } catch (error) {
      console.error('Failed to create session:', error);
      throw new Error('Failed to initialize chat session');
    }
  }

  static getCurrentSessionId(): string | null {
    return sessionStorage.getItem(this.SESSION_STORAGE_KEY);
  }

  static clearSession(): void {
    sessionStorage.removeItem(this.SESSION_STORAGE_KEY);
  }

  static async switchToNewSession(): Promise<string> {
    this.clearSession();
    return this.getOrCreateSession();
  }

  static async validateSession(sessionId: string): Promise<boolean> {
    try {
      await ApiClient.getSessionHistory(sessionId);
      return true;
    } catch (error) {
      return false;
    }
  }
}
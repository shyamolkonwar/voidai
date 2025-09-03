'use client';

import { useState, useCallback, useEffect } from 'react';

export function useSession() {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load session from URL on mount
  useEffect(() => {
    const pathParts = window.location.pathname.split('/');
    if (pathParts.length >= 3 && pathParts[1] === 'chat') {
      const sessionId = pathParts[2];
      if (sessionId && sessionId !== 'undefined') {
        setCurrentSessionId(sessionId);
        // Store session ID in localStorage for persistence
        localStorage.setItem('currentSessionId', sessionId);
      }
    }
  }, []);

  // Load session from localStorage on mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('currentSessionId');
    if (savedSessionId && !currentSessionId) {
      setCurrentSessionId(savedSessionId);
    }
  }, [currentSessionId]);

  const createSession = useCallback(async (): Promise<string> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://127.0.0.1:8001/api/v1/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to create session: ${response.status}`);
      }

      const data = await response.json();
      const newSessionId = data.session_id;

      setCurrentSessionId(newSessionId);
      localStorage.setItem('currentSessionId', newSessionId);
      
      return newSessionId;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create session';
      setError(errorMessage);
      
      // Fallback: generate a local session ID
      const fallbackSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      setCurrentSessionId(fallbackSessionId);
      localStorage.setItem('currentSessionId', fallbackSessionId);
      
      return fallbackSessionId;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadSessionHistory = useCallback(async (sessionId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`http://127.0.0.1:8001/api/v1/sessions/${sessionId}/history`);
      
      if (!response.ok) {
        throw new Error(`Failed to load session history: ${response.status}`);
      }

      const data = await response.json();
      return data.messages;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load session history';
      setError(errorMessage);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearSession = useCallback(() => {
    setCurrentSessionId(null);
    localStorage.removeItem('currentSessionId');
  }, []);

  const getSessionUrl = useCallback((sessionId: string) => {
    return `/chat/${sessionId}`;
  }, []);

  const navigateToSession = useCallback((sessionId: string) => {
    // Return the session URL - let the calling component handle navigation
    return getSessionUrl(sessionId);
  }, [getSessionUrl]);

  return {
    currentSessionId,
    isLoading,
    error,
    createSession,
    loadSessionHistory,
    clearSession,
    getSessionUrl,
    navigateToSession,
  };
}
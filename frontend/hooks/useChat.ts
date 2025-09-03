'use client';

import { useState, useCallback } from 'react';
import { ChatMessage, ApiResponse } from '@/types/chat';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (query: string, sessionId?: string) => {
    if (!query.trim()) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const requestBody: any = { query };
      if (sessionId) {
        requestBody.session_id = sessionId;
      }

      console.log('Sending query to backend:', requestBody);
      const response = await fetch('http://127.0.0.1:8001/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log('Backend response status:', response.status);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const responseData = await response.json();
      console.log('Backend response data structure:', JSON.stringify(responseData, null, 2));
      
      // Check if the response has the expected structure
      const data: ApiResponse = {
        type: responseData.type || 'text',
        data: responseData.data || [],
        summary: responseData.summary || responseData.reasoning || 'No summary available'
      };

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.summary,
        timestamp: new Date(),
        response: data,
      };

      setMessages(prev => [...prev, assistantMessage]);
      return [...messages, userMessage, assistantMessage];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date(),
        response: {
          type: 'text',
          summary: 'Error: Unable to process request',
        },
      };

      setMessages(prev => [...prev, errorMessage]);
      return [...messages, userMessage, errorMessage];
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const setMessagesDirectly = useCallback((newMessages: ChatMessage[]) => {
    setMessages(newMessages);
  }, []);
  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
    setMessagesDirectly,
  };
}
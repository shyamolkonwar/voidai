'use client';

import { useState, useCallback } from 'react';
import { ChatMessage, ApiResponse } from '@/types/chat';

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = useCallback(async (sessionId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const historyResponse = await fetch(`http://127.0.0.1:8001/api/v1/sessions/${sessionId}/history`);
      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        const sessionMessages: ChatMessage[] = historyData.messages.map((msg: any) => {
          const messageObj: ChatMessage = {
            id: `${msg.role}-${Date.now()}-${Math.random()}`,
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.timestamp || Date.now()),
          };
          
          // For assistant messages, include the full response data for visualizations
          if (msg.role === 'assistant' && msg.full_response) {
            messageObj.response = {
              type: msg.full_response.type || 'text',
              data: msg.full_response.data || [],
              summary: msg.full_response.summary || msg.full_response.reasoning || 'No summary available',
              // Include additional response metadata
              sql_query: msg.full_response.sql_query,
              row_count: msg.full_response.row_count,
              confidence_score: msg.full_response.confidence_score,
              execution_time: msg.full_response.execution_time,
              reasoning: msg.full_response.reasoning,
              success: msg.full_response.success,
              // Store the complete response data for future context retrieval
              full_response: msg.full_response
            };
          } else if (msg.response) {
            // Preserve existing response format for backward compatibility
            messageObj.response = msg.response;
          }
          
          return messageObj;
        });
        setMessages(sessionMessages);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [setMessages]);

  const sendInitialMessage = useCallback(async (query: string, sessionId: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: query,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const responseData = await response.json();
      
      if (responseData.messages && responseData.messages.length > 0) {
        const assistantMessages = responseData.messages.filter((msg: ChatMessage) => msg.role === 'assistant');
        const latestAssistantMessage = assistantMessages[assistantMessages.length - 1];
        
        if (latestAssistantMessage) {
          setMessages(prev => [...prev, latestAssistantMessage]);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [setMessages]);

  const sendMessage = useCallback(async (query: string, sessionId?: string): Promise<ChatMessage[]> => {
    if (!query.trim()) return [];

    setIsLoading(true);
    setError(null);

    try {
      const requestBody: any = { query };
      if (sessionId) {
        requestBody.session_id = sessionId;
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 seconds timeout

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          sessionId,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const responseData = await response.json();
      
      let newMessages: ChatMessage[] = [];
      if (responseData.messages && responseData.messages.length > 0) {
        const assistantMessages = responseData.messages.filter((msg: ChatMessage) => msg.role === 'assistant');
        const latestAssistantMessage = assistantMessages[assistantMessages.length - 1];
        
        if (latestAssistantMessage) {
          setMessages(prev => {
            newMessages = [...prev, latestAssistantMessage];
            return newMessages;
          });
        }
      }
      return newMessages;
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

      let newMessages: ChatMessage[] = [];
      setMessages(prev => {
        newMessages = [...prev, errorMessage];
        return newMessages;
      });
      return newMessages;
    } finally {
      setIsLoading(false);
    }
  }, [setMessages]);

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
    sendInitialMessage,
    loadHistory,
    clearChat,
    setMessagesDirectly,
  };
}
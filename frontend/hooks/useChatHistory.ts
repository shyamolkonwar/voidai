'use client';

import { useState, useCallback, useEffect } from 'react';
import { Chat, ChatMessage } from '@/types/chat';

export function useChatHistory() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load chats from backend on mount
  useEffect(() => {
    const loadChats = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('http://127.0.0.1:8001/api/v1/sessions');
        if (response.ok) {
          const data = await response.json();
          // Convert backend session format to frontend chat format
          const formattedChats: Chat[] = data.sessions.map((session: any) => ({
            id: session.id,
            title: session.title || 'New Chat',
            messages: [], // Messages are loaded separately when needed
            createdAt: new Date(session.last_activity || Date.now()),
            updatedAt: new Date(session.last_activity || Date.now()),
          }));
          setChats(formattedChats);
        } else {
          console.error('Failed to load chat sessions:', response.status);
        }
      } catch (error) {
        console.error('Failed to load chat sessions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadChats();
  }, []);

  const createNewChat = useCallback(async () => {
    try {
      const response = await fetch('http://127.0.0.1:8001/api/v1/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const sessionId = data.session_id;
        
        const newChat: Chat = {
          id: sessionId,
          title: 'New Chat',
          messages: [],
          createdAt: new Date(data.created_at || Date.now()),
          updatedAt: new Date(data.created_at || Date.now()),
        };

        setChats(prev => [newChat, ...prev]);
        setCurrentChatId(sessionId);
        return sessionId;
      } else {
        throw new Error('Failed to create session');
      }
    } catch (error) {
      console.error('Failed to create new chat session:', error);
      // Fallback to local UUID generation if backend fails
      const fallbackId = `chat-${Date.now()}`;
      const newChat: Chat = {
        id: fallbackId,
        title: 'New Chat',
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date(),
      };
      setChats(prev => [newChat, ...prev]);
      setCurrentChatId(fallbackId);
      return fallbackId;
    }
  }, []);

  const updateChat = useCallback((chatId: string, messages: ChatMessage[]) => {
    setChats(prev => {
      const chatExists = prev.some(chat => chat.id === chatId);
      if (chatExists) {
        return prev.map(chat => {
          if (chat.id === chatId) {
            const updatedChat = {
              ...chat,
              messages,
              updatedAt: new Date(),
            };

            if (messages.length > 0 && chat.title === 'New Chat') {
              const firstUserMessage = messages.find(msg => msg.role === 'user');
              if (firstUserMessage) {
                updatedChat.title = firstUserMessage.content.slice(0, 50) + 
                  (firstUserMessage.content.length > 50 ? '...' : '');
              }
            }

            return updatedChat;
          }
          return chat;
        });
      } else {
        const firstUserMessage = messages.find(msg => msg.role === 'user');
        const newChat: Chat = {
          id: chatId,
          title: firstUserMessage ? firstUserMessage.content.slice(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '') : 'New Chat',
          messages,
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        return [newChat, ...prev];
      }
    });
  }, []);

  const deleteChat = useCallback(async (chatId: string) => {
    try {
      const response = await fetch(`http://127.0.0.1:8001/api/v1/sessions/${chatId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setChats(prev => {
          const filtered = prev.filter(chat => chat.id !== chatId);
          
          // If we deleted the current chat, switch to the next available one
          if (chatId === currentChatId) {
            setCurrentChatId(filtered.length > 0 ? filtered[0].id : null);
          }
          
          return filtered;
        });
      } else {
        console.error('Failed to delete chat session:', response.status);
      }
    } catch (error) {
      console.error('Failed to delete chat session:', error);
    }
  }, [currentChatId, setChats, setCurrentChatId]);

  const getCurrentChat = useCallback(() => {
    return chats.find(chat => chat.id === currentChatId) || null;
  }, [chats, currentChatId]);

  return {
    chats,
    currentChatId,
    setCurrentChatId,
    createNewChat,
    updateChat,
    deleteChat,
    getCurrentChat,
    isLoading,
  };
}
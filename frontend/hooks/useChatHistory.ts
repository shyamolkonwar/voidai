'use client';

import { useState, useCallback, useEffect } from 'react';
import { Chat, ChatMessage } from '@/types/chat';

export function useChatHistory() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);

  // Load chats from localStorage on mount
  useEffect(() => {
    const savedChats = localStorage.getItem('void-chats');
    if (savedChats) {
      try {
        const parsedChats = JSON.parse(savedChats).map((chat: any) => ({
          ...chat,
          createdAt: new Date(chat.createdAt),
          updatedAt: new Date(chat.updatedAt),
          messages: chat.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          })),
        }));
        setChats(parsedChats);
        
        // Set the most recent chat as current
        if (parsedChats.length > 0) {
          setCurrentChatId(parsedChats[0].id);
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    }
  }, []);

  // Save chats to localStorage whenever chats change
  useEffect(() => {
    if (chats.length > 0) {
      localStorage.setItem('void-chats', JSON.stringify(chats));
    }
  }, [chats]);

  const createNewChat = useCallback(() => {
    const newChat: Chat = {
      id: `chat-${Date.now()}`,
      title: 'New Chat',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    setChats(prev => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
    return newChat.id;
  }, []);

  const updateChat = useCallback((chatId: string, messages: ChatMessage[]) => {
    setChats(prev => prev.map(chat => {
      if (chat.id === chatId) {
        const updatedChat = {
          ...chat,
          messages,
          updatedAt: new Date(),
        };

        // Update title based on first user message
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
    }));
  }, []);

  const deleteChat = useCallback((chatId: string) => {
    setChats(prev => {
      const filtered = prev.filter(chat => chat.id !== chatId);
      
      // If we deleted the current chat, switch to the next available one
      if (chatId === currentChatId) {
        setCurrentChatId(filtered.length > 0 ? filtered[0].id : null);
      }
      
      return filtered;
    });
  }, [currentChatId]);

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
  };
}
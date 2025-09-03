'use client';

import { useState, useCallback, useEffect } from 'react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { useChatHistory } from '@/hooks/useChatHistory';
import { useChat } from '@/hooks/useChat';
import { ChatMessage } from '@/types/chat';

export default function Home() {
  const {
    chats,
    currentChatId,
    setCurrentChatId,
    createNewChat,
    updateChat,
    deleteChat,
    getCurrentChat,
  } = useChatHistory();
  
  const { messages, isLoading, sendMessage, setMessagesDirectly } = useChat();
  
  // Sync messages with current chat
  useEffect(() => {
    const currentChat = getCurrentChat();
    if (currentChat) {
      setMessagesDirectly(currentChat.messages);
    } else {
      setMessagesDirectly([]);
    }
  }, [currentChatId, getCurrentChat, setMessagesDirectly]);
  
  // Update chat history when messages change
  useEffect(() => {
    if (currentChatId && messages.length > 0) {
      updateChat(currentChatId, messages);
    }
  }, [messages, currentChatId, updateChat]);

  const handleSendMessage = useCallback(async (query: string) => {
    // Create new chat if none exists
    let chatId = currentChatId;
    if (!chatId) {
      chatId = createNewChat();
    }
    
    const newMessages = await sendMessage(query);
    if (newMessages && chatId) {
      updateChat(chatId, newMessages);
    }
  }, [currentChatId, createNewChat, sendMessage, updateChat]);

  const handleChatSelect = useCallback((chatId: string) => {
    setCurrentChatId(chatId);
  }, [setCurrentChatId]);

  const handleDeleteChat = useCallback((chatId: string) => {
    deleteChat(chatId);
  }, [deleteChat]);

  const handleNewChat = useCallback(() => {
    createNewChat();
  }, [createNewChat]);

  return (
    <div className="h-full bg-black flex">
      <Sidebar
        chats={chats}
        currentChatId={currentChatId}
        onChatSelect={handleChatSelect}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
      />
      <div className="flex-1">
        <ChatInterface
          messages={messages}
          isLoading={isLoading}
          onSendMessage={handleSendMessage}
        />
      </div>
    </div>
  );
}
'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { useChatHistory } from '@/hooks/useChatHistory';
import { useChat } from '@/hooks/useChat';
import { ChatMessage } from '@/types/chat';

export default function Home() {
  const router = useRouter();
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
    let chatIdToUse = currentChatId;
    
    // If no current chat, create a new one automatically
    if (!chatIdToUse) {
      chatIdToUse = await createNewChat();
      setCurrentChatId(chatIdToUse);
      
      // Navigate to the new chat session without page reload
      router.push(`/chat/${chatIdToUse}`);
    }
    
    const newMessages = await sendMessage(query, chatIdToUse!);
    if (newMessages && chatIdToUse) {
      updateChat(chatIdToUse, newMessages);
    }
  }, [currentChatId, sendMessage, updateChat, createNewChat, setCurrentChatId, router]);

  const handleChatSelect = useCallback((chatId: string) => {
    setCurrentChatId(chatId);
  }, [setCurrentChatId]);

  const handleDeleteChat = useCallback((chatId: string) => {
    deleteChat(chatId);
  }, [deleteChat]);


  return (
    <div className="h-full bg-black flex">
      <Sidebar
        chats={chats}
        currentChatId={currentChatId}
        onChatSelect={handleChatSelect}
        onDeleteChat={handleDeleteChat}
        isHomePage={true}
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
'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { useChatHistory } from '@/hooks/useChatHistory';
import { useChat } from '@/hooks/useChat';
import { ChatMessage } from '@/types/chat';
import { checkServerReady, ServerStatus } from '@/utils/serverHealth';


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
  const [serverStatus, setServerStatus] = useState<ServerStatus>({
    isOnline: false,
    lastChecked: null,
  });
  const [serverCheckLoading, setServerCheckLoading] = useState(false);
  
  // Clear current chat and messages when on home page
  useEffect(() => {
    setCurrentChatId(null);
    setMessagesDirectly([]);
  }, [setCurrentChatId, setMessagesDirectly]);

  // Sync messages with current chat (only if we have a current chat)
  useEffect(() => {
    if (currentChatId) {
      const currentChat = getCurrentChat();
      if (currentChat) {
        setMessagesDirectly(currentChat.messages);
      }
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

  // Check server status on mount and periodically
  useEffect(() => {
    const checkServer = async () => {
      setServerCheckLoading(true);
      const status = await checkServerReady();
      setServerStatus(status);
      setServerCheckLoading(false);
    };

    checkServer();

    // Check every 30 seconds
    const interval = setInterval(checkServer, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSendMessage = useCallback(async (query: string) => {
    // If we are on the home page, create a new chat and navigate
    if (!currentChatId) {
      try {
        const newChatId = await createNewChat();
        if (newChatId) {
          router.push(`/chat/${newChatId}?q=${encodeURIComponent(query)}`);
        } else {
          // Handle error: show a toast or an alert
          console.error("Failed to create a new chat.");
        }
      } catch (error) {
        console.error("Error creating new chat:", error);
      }
    } else {
      // This case should ideally not be hit from the home page
      // but as a fallback, we can navigate to the existing chat with the new query
      router.push(`/chat/${currentChatId}?q=${encodeURIComponent(query)}`);
    }
  }, [currentChatId, createNewChat, router]);

  const handleChatSelect = useCallback((chatId: string) => {
    setCurrentChatId(chatId);
    router.push(`/chat/${chatId}`);
  }, [setCurrentChatId, router]);

  const handleDeleteChat = useCallback(async (chatId: string) => {
    await deleteChat(chatId);
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
            serverStatus={serverStatus}
            serverCheckLoading={serverCheckLoading}
          />
      </div>
    </div>
  );
}
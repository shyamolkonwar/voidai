'use client';

import { useState, useCallback, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { useChatHistory } from '@/hooks/useChatHistory';
import { useChat } from '@/hooks/useChat';
import { ChatMessage } from '@/types/chat';

export default function ChatSessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.session_id as string;
  
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
  
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);

  // Load session history from backend on mount
  useEffect(() => {
    const loadSessionHistory = async () => {
      try {
        setIsLoadingHistory(true);
        console.log(`Loading session history for: ${sessionId}`);
        const response = await fetch(`http://127.0.0.1:8001/api/v1/sessions/${sessionId}/history`);
        
        console.log(`Session history response status: ${response.status}`);
        if (response.ok) {
          const data = await response.json();
          console.log(`Session history data:`, data);
          
          // Convert backend messages to frontend format
          const sessionMessages: ChatMessage[] = data.messages.map((msg: any) => ({
            id: `${msg.role}-${Date.now()}-${Math.random()}`,
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.timestamp || Date.now()),
          }));
          
          console.log(`Converted ${sessionMessages.length} messages`);
          setMessagesDirectly(sessionMessages);
          
          // Update or create local chat entry
          const existingChat = chats.find(chat => chat.id === sessionId);
          if (existingChat) {
            updateChat(sessionId, sessionMessages);
          } else {
            // Create a new chat entry for this session
            const newChat = {
              id: sessionId,
              title: `Session ${sessionId.slice(0, 8)}...`,
              messages: sessionMessages,
              createdAt: new Date(),
              updatedAt: new Date(),
            };
            console.log('New chat created locally');
          }
          
          setCurrentChatId(sessionId);
        } else {
          console.error('Failed to load session history');
          // Create a new empty chat for this session
          setMessagesDirectly([]);
          setCurrentChatId(sessionId);
        }
      } catch (error) {
        console.error('Error loading session history:', error);
        setMessagesDirectly([]);
        setCurrentChatId(sessionId);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    if (sessionId) {
      loadSessionHistory();
    }
  }, [sessionId, setMessagesDirectly, setCurrentChatId, chats, updateChat]);

  // Update chat history when messages change
  useEffect(() => {
    if (currentChatId && messages.length > 0) {
      updateChat(currentChatId, messages);
    }
  }, [messages, currentChatId, updateChat]);

  const handleSendMessage = useCallback(async (query: string) => {
    const newMessages = await sendMessage(query, sessionId);
    if (newMessages && sessionId) {
      updateChat(sessionId, newMessages);
    }
  }, [sessionId, sendMessage, updateChat]);

  const handleChatSelect = useCallback((chatId: string) => {
    setCurrentChatId(chatId);
    // Navigate to the selected chat session without page reload
    router.push(`/chat/${chatId}`);
  }, [setCurrentChatId, router]);

  const handleDeleteChat = useCallback((chatId: string) => {
    deleteChat(chatId);
    // If we're deleting the current chat, navigate to home
    if (chatId === sessionId) {
      router.push('/');
    }
  }, [deleteChat, sessionId]);


  // Don't show loading screen - show the chat interface immediately
  // and load history in background

  return (
    <div className="h-full bg-black flex">
      <Sidebar
       chats={chats}
       currentChatId={currentChatId}
       onChatSelect={handleChatSelect}
       onDeleteChat={handleDeleteChat}
       isHomePage={false}
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
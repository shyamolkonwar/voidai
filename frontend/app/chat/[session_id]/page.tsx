'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { Sidebar } from '@/components/sidebar/Sidebar';
import { useChatHistory } from '@/hooks/useChatHistory';
import { useChat } from '@/hooks/useChat';

export default function ChatSessionPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = params.session_id as string;
  const initialQuery = searchParams.get('q');

  const {
    chats,
    currentChatId,
    setCurrentChatId,
    updateChat,
    deleteChat,
  } = useChatHistory();
  
  const { messages, isLoading, sendMessage, sendInitialMessage, loadHistory } = useChat();

  const initialMessageSent = useRef(false);

  useEffect(() => {
    if (initialQuery && sessionId && !initialMessageSent.current) {
      initialMessageSent.current = true;
      sendInitialMessage(initialQuery, sessionId);
      router.replace(`/chat/${sessionId}`, { scroll: false });
    } else if (sessionId && !initialQuery) {
      loadHistory(sessionId);
    }
  }, [initialQuery, sessionId, sendInitialMessage, loadHistory, router]);

  const handleSendMessage = useCallback(async (query: string) => {
    await sendMessage(query, sessionId);
  }, [sessionId, sendMessage]);

  const handleChatSelect = useCallback((chatId: string) => {
    setCurrentChatId(chatId);
    router.push(`/chat/${chatId}`);
  }, [setCurrentChatId, router]);

  const handleDeleteChat = useCallback((chatId: string) => {
    deleteChat(chatId);
    if (chatId === sessionId) {
      router.push('/');
    }
  }, [deleteChat, sessionId]);

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
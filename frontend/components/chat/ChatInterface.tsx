'use client';

import { useState, useRef, useEffect, useMemo } from 'react';
import { Send } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { ChatMessage as ChatMessageType } from '@/types/chat';

interface ChatInterfaceProps {
  messages: ChatMessageType[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  serverStatus?: {
    isOnline: boolean;
    lastChecked: Date | null;
    error?: string;
  };
  serverCheckLoading?: boolean;
}

export function ChatInterface({
  messages,
  isLoading,
  onSendMessage,
  serverStatus,
  serverCheckLoading = false
}: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
      });
    }
  };

  useEffect(() => {
    // Only scroll to bottom if it's a new message or loading state
    if (messages.length > 0 || isLoading) {
      const timer = setTimeout(() => {
        scrollToBottom();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [messages, isLoading]);


  const displayMessages = useMemo(() => {
    if (isLoading) {
      const thinkingMessage: ChatMessageType = {
        id: 'thinking',
        role: 'assistant',
        content: 'VOID is thinking...',
        timestamp: new Date(),
        isLoading: true,
      };
      return [...messages, thinkingMessage];
    }
    return messages;
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const query = input.trim();
    setInput('');
    await onSendMessage(query);
    
    // Focus back to input after sending
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full bg-black">
      {/* Permanent server status indicator */}
      <div className="border-b border-gray-800">
        {serverCheckLoading && (
          <div className="bg-yellow-900 text-yellow-100 p-2 text-sm">
            <div className="flex items-center justify-center gap-2">
              <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
              <span>Checking server status...</span>
            </div>
          </div>
        )}
        
        {serverStatus && !serverStatus.isOnline && !serverCheckLoading && (
          <div className="bg-red-900 text-red-100 p-2 text-sm">
            <div className="flex items-center justify-center gap-2">
              <div className="w-2 h-2 bg-red-400 rounded-full"></div>
              <span>
                Server offline - {serverStatus.error || 'Cannot create new chats'}
              </span>
            </div>
          </div>
        )}
        
        {serverStatus && serverStatus.isOnline && (
          <div className="bg-green-900 text-green-100 p-2 text-sm">
            <div className="flex items-center justify-center gap-2">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span>Server online - Ready for queries</span>
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full p-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
                <Send className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-white mb-2">
                Welcome to VOID
              </h3>
              <p className="text-gray-400 text-sm max-w-sm">
                Ask questions about ocean data and receive visual insights.
                Try asking about temperature, salinity, or marine observations.
              </p>
            </div>
          </div>
        ) : (
          <div className="min-h-full">
            {displayMessages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-800">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about ocean data..."
            disabled={isLoading}
            className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-1 focus:ring-gray-600 focus:border-gray-600 text-white placeholder-gray-400 disabled:bg-gray-900 disabled:text-gray-500"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-4 py-3 bg-white text-black rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-1 focus:ring-gray-600 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center min-w-[44px]"
          >
            {isLoading ? (
              <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
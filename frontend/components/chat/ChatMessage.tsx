'use client';

import { ChatMessage as ChatMessageType } from '@/types/chat';
import { User, Bot } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  return (
    <div className={`flex gap-4 p-6 ${message.role === 'user' ? 'bg-gray-900' : 'bg-black'}`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        message.role === 'user' ? 'bg-white text-black' : 'bg-gray-700 text-white'
      }`}>
        {message.role === 'user' ? (
          <User className="w-4 h-4" />
        ) : (
          <Bot className="w-4 h-4" />
        )}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="text-white leading-relaxed">
          {message.content}
        </div>
      </div>
    </div>
  );
}
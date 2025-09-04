'use client';

import { ChatMessage as ChatMessageType } from '@/types/chat';
import { User, Bot } from 'lucide-react';
import { MapVisualization } from '@/components/visualizations/MapVisualization';
import { TableVisualization } from '@/components/visualizations/TableVisualization';
import { TextVisualization } from '@/components/visualizations/TextVisualization';

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  if (message.isLoading) {
    return (
      <div className="flex gap-4 p-6 bg-black">
        <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-700 text-white">
          <Bot className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-white leading-relaxed mb-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
              <div className="w-2 h-2 bg-white rounded-full animate-pulse delay-75"></div>
              <div className="w-2 h-2 bg-white rounded-full animate-pulse delay-150"></div>
              <span className="ml-2">VOID is thinking...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
        <div className="text-white leading-relaxed mb-4">
          {message.content}
        </div>
        
        {message.role === 'assistant' && message.response && (
          <div className="mt-4">
            {message.response.type === 'map' && (
              <MapVisualization data={message.response.data} summary={message.response.summary} />
            )}
            
            {message.response.type === 'table' && (
              <TableVisualization data={message.response.data} summary={message.response.summary} />
            )}
            
            {message.response.type === 'text' && (
              <TextVisualization summary={message.response.summary} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
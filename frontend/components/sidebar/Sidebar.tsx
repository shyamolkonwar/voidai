'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Plus, MessageSquare, Trash2, Menu, X } from 'lucide-react';
import { Chat } from '@/types/chat';

interface SidebarProps {
  chats: Chat[];
  currentChatId: string | null;
  onChatSelect: (chatId: string) => void;
  onNewChat?: () => void;
  onDeleteChat: (chatId: string) => void;
  isHomePage?: boolean;
}

export function Sidebar({
  chats,
  currentChatId,
  onChatSelect,
  onNewChat,
  onDeleteChat,
  isHomePage = false
}: SidebarProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  
  // Check if we're on a mobile device and handle responsive behavior
  const [isMobile, setIsMobile] = useState(false);
  
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      // On desktop, sidebar should always be open
      if (!mobile) {
        setIsOpen(true);
      }
    };
    
    // Check initial screen size
    checkMobile();
    
    // Add resize listener
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const toggleSidebar = () => setIsOpen(!isOpen);

  const handleChatSelect = (chatId: string) => {
    onChatSelect(chatId);
    setIsOpen(false); // Close sidebar on mobile after selection
  };


  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={toggleSidebar}
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-gray-800 text-white rounded-md hover:bg-gray-700 transition-colors"
      >
        {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed md:relative inset-y-0 left-0 z-40 w-64 bg-black border-r border-gray-800 
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-xl font-bold text-white">VOID</h1>
            </div>
            
            <Link
              href="/"
              className={`w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md transition-colors ${
                isHomePage
                  ? 'text-gray-500 bg-gray-900 cursor-not-allowed pointer-events-none'
                  : 'text-white bg-gray-800 hover:bg-gray-700 cursor-pointer'
              }`}
            >
              <Plus className="w-4 h-4" />
              New Chat
            </Link>
          </div>

          {/* Chat History */}
          <div className="flex-1 overflow-y-auto p-2">
            {chats.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No conversations yet</p>
              </div>
            ) : (
              <div className="space-y-1">
                {chats.map((chat) => (
                  <div
                    key={chat.id}
                    className={`group relative flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors ${
                      currentChatId === chat.id
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-300 hover:bg-gray-900 hover:text-white'
                    }`}
                    onClick={() => handleChatSelect(chat.id)}
                  >
                    <MessageSquare className="w-4 h-4 flex-shrink-0" />
                    <span className="flex-1 text-sm truncate">
                      {chat.title}
                    </span>
                    
                    {currentChatId === chat.id && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteChat(chat.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-400 transition-all"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-gray-800">
            <div className="text-xs text-gray-500 text-center">
              Ocean Data Assistant
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Chat } from "./ChatShell";

interface SidebarProps {
  chats: Chat[];
  currentChatId: string;
  onNewChat: () => void;
  onSelectChat: (chatId: string) => void;
  onDeleteChat: (chatId: string) => void;
}

export default function Sidebar({ chats, currentChatId, onNewChat, onSelectChat, onDeleteChat }: SidebarProps) {
  const [open, setOpen] = useState(true);
  const [showText, setShowText] = useState(true);
  const router = useRouter();

  const handleClose = () => {
    setShowText(false);
    setTimeout(() => setOpen(false), 150);
  };

  const handleOpen = () => {
    setOpen(true);
    setTimeout(() => setShowText(true), 150);
  };

  return (
    <div className="relative h-full">
      <AnimatePresence initial={false}>
        {open ? (
          <motion.aside
            key="open"
            initial={{ width: 64, opacity: 1 }}
            animate={{ width: 280, opacity: 1 }}
            exit={{ width: 64, opacity: 1 }}
            transition={{ type: "spring", stiffness: 300, damping: 30, duration: 0.3 }}
            className="h-full border-r border-white/10 bg-black overflow-hidden"
          >
            {/* top row */}
            <motion.div 
              className="flex items-center justify-between px-3 py-3"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
            >
              <motion.button 
                onClick={() => router.push('/')}
                className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center font-bold">
                  V
                </div>
              </motion.button>
              <motion.button
                aria-label="Close sidebar"
                onClick={handleClose}
                className="p-2 rounded hover:bg-white/10 transition-colors duration-200"
                whileHover={{ scale: 1.1, backgroundColor: "rgba(255,255,255,0.1)" }}
                whileTap={{ scale: 0.9 }}
              >
                <motion.svg 
                  width="18" 
                  height="18" 
                  viewBox="0 0 24 24" 
                  fill="none"
                  animate={{ rotate: 0 }}
                  whileHover={{ rotate: -10 }}
                >
                  <path d="M15 6l-6 6 6 6" stroke="white" strokeWidth="1.4" strokeLinecap="round" />
                </motion.svg>
              </motion.button>
            </motion.div>

            {/* New chat */}
            <motion.div 
              className="px-2"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
            >
              <motion.button 
                onClick={onNewChat}
                className="w-full h-10 border border-white/20 rounded-lg text-sm flex items-center justify-center gap-2 hover:border-white/30 transition-colors duration-200"
                whileHover={{ scale: 1.02, borderColor: "rgba(255,255,255,0.4)" }}
                whileTap={{ scale: 0.98 }}
              >
                <motion.div
                  className="w-4 h-4 flex items-center justify-center"
                  whileHover={{ rotate: 90 }}
                  transition={{ duration: 0.2 }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M12 5v14M5 12h14" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </motion.div>
                <AnimatePresence>
                  {showText && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: "auto" }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ duration: 0.2 }}
                      className="whitespace-nowrap text-white/80"
                    >
                      New Chat
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.button>
            </motion.div>

            {/* history */}
            <motion.div 
              className="mt-4 flex-1 overflow-y-auto px-2 space-y-1 sidebar-scrollbar"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              style={{ height: 'calc(100vh - 180px)' }}
            >
              {chats.map((chat, index) => {
                const isActive = chat.id === currentChatId;
                return (
                  <motion.div
                    key={chat.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: showText ? 1 : 0, x: showText ? 0 : -20 }}
                    transition={{ duration: 0.2, delay: 0.3 + index * 0.05 }}
                    className="relative group"
                  >
                    <motion.button
                      onClick={() => onSelectChat(chat.id)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors duration-200 ${
                        isActive 
                          ? 'bg-white/10 text-white border-l-2 border-white/40' 
                          : 'text-white/80 hover:bg-white/5'
                      }`}
                      whileHover={{ scale: 1.02, backgroundColor: isActive ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.08)" }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <motion.div className="truncate pr-8">
                        {showText ? chat.title : ''}
                      </motion.div>
                    </motion.button>
                    
                    {/* Delete button */}
                    {showText && chats.length > 1 && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteChat(chat.id);
                        }}
                        className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-70 p-1 rounded-sm hover:bg-red-500/20 hover:opacity-100 transition-all duration-150"
                      >
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                          <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                        </svg>
                      </button>
                    )}
                  </motion.div>
                );
              })}
            </motion.div>

            {/* profile */}
            <motion.div 
              className="absolute bottom-0 left-0 right-0 p-3 border-t border-white/10 bg-black"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 }}
            >
              <motion.div className="flex items-center justify-between">
                <motion.div 
                  className="flex items-center gap-2"
                  whileHover={{ scale: 1.05 }}
                >
                  <img
                    src="https://avatars.githubusercontent.com/u/1?v=4"
                    alt="you"
                    className="w-8 h-8 rounded-full"
                  />
                  <AnimatePresence>
                    {showText && (
                      <motion.div 
                        className="text-xs"
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: "auto" }}
                        exit={{ opacity: 0, width: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div className="text-white/90">You</div>
                        <div className="text-white/50">Premium</div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              </motion.div>
            </motion.div>
          </motion.aside>
        ) : (
          // collapsed
          <motion.aside
            key="closed"
            initial={{ width: 280 }}
            animate={{ width: 64 }}
            exit={{ width: 280 }}
            transition={{ type: "spring", stiffness: 300, damping: 30, duration: 0.3 }}
            className="h-full border-r border-white/10 bg-black flex flex-col items-center overflow-hidden"
          >
            <motion.button
              aria-label="Open sidebar"
              onClick={handleOpen}
              className="mt-3 p-2 rounded hover:bg-white/10 transition-colors duration-200"
              whileHover={{ scale: 1.1, backgroundColor: "rgba(255,255,255,0.1)" }}
              whileTap={{ scale: 0.9 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
            >
              <motion.svg 
                width="18" 
                height="18" 
                viewBox="0 0 24 24" 
                fill="none"
                animate={{ rotate: 0 }}
                whileHover={{ rotate: 10 }}
              >
                <path d="M9 6l6 6-6 6" stroke="white" strokeWidth="1.4" strokeLinecap="round" />
              </motion.svg>
            </motion.button>

            {/* New chat button for minimized sidebar */}
            <motion.button 
              onClick={onNewChat}
              className="mt-4 w-10 h-10 rounded-lg border border-white/20 hover:border-white/40 transition-colors duration-200 flex items-center justify-center text-white"
              aria-label="New chat"
              whileHover={{ scale: 1.1, borderColor: "rgba(255,255,255,0.4)" }}
              whileTap={{ scale: 0.9 }}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15 }}
            >
              <motion.div
                whileHover={{ rotate: 90 }}
                transition={{ duration: 0.2 }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M12 5v14M5 12h14" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </motion.div>
            </motion.button>

            <motion.div 
              className="mt-auto mb-3"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              whileHover={{ scale: 1.1 }}
            >
              <img
                src="https://avatars.githubusercontent.com/u/1?v=4"
                alt="you"
                className="w-8 h-8 rounded-full"
              />
            </motion.div>
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  );
}

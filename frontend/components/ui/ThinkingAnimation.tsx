'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';

export function ThinkingAnimation() {
  return (
    <div className="flex items-center justify-start p-3">
      <div className="bg-gray-800 rounded-2xl rounded-tl-sm p-4 flex items-center shadow-lg">
        <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-gray-700 text-white mr-3">
          <Bot className="w-4 h-4" />
        </div>
        
        <div className="flex space-x-2 mr-3">
          <motion.div
            className="w-3 h-3 bg-blue-400 rounded-full"
            animate={{
              y: [0, -8, 0],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
              repeatType: 'loop',
              delay: 0,
            }}
          />
          <motion.div
            className="w-3 h-3 bg-blue-500 rounded-full"
            animate={{
              y: [0, -8, 0],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
              repeatType: 'loop',
              delay: 0.2,
            }}
          />
          <motion.div
            className="w-3 h-3 bg-blue-600 rounded-full"
            animate={{
              y: [0, -8, 0],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
              repeatType: 'loop',
              delay: 0.4,
            }}
          />
        </div>
        <div className="text-sm text-gray-300 font-medium">VOID is thinking...</div>
      </div>
    </div>
  );
}
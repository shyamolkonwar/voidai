// components/GlassCard.tsx
"use client";

import React from "react";
import { motion, HTMLMotionProps } from "framer-motion";

const MotionDiv = motion.div as React.FC<HTMLMotionProps<"div"> & React.HTMLAttributes<HTMLDivElement>>;

const ContentPreview = ({ title }: { title: string }) => {
  switch (title) {
    case "ASK. DON'T CODE":
      return (
        <div className="w-full h-32 bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
          <div className="p-3">
            <div className="bg-blue-900/30 p-2 rounded text-xs text-blue-200 font-mono">
              <div className="text-green-400">$</div>
              <div className="ml-2">Show me salinity profiles near equator March 2023</div>
              <div className="text-green-400 mt-1">→</div>
              <div className="ml-2 text-white">Processing your natural language query...</div>
            </div>
          </div>
        </div>
      );
    
    case "SEE. DON'T GUESS":
      return (
        <div className="w-full h-32 bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
          <div className="p-3 flex items-center justify-center h-full">
            <div className="flex items-center space-x-2 text-blue-300">
              <div className="w-4 h-4 border-2 border-blue-400 rounded"></div>
              <span className="text-sm">Generating visualization...</span>
              <div className="animate-pulse w-3 h-3 bg-blue-400 rounded-full"></div>
            </div>
          </div>
        </div>
      );
    
    case "SHARE. DON'T HOARD":
      return (
        <div className="w-full h-32 bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
          <div className="p-3">
            <div className="flex items-center space-x-2 text-sm">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white">R</div>
              <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center text-white">S</div>
              <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-white">L</div>
              <div className="text-gray-400">+3 collaborators</div>
            </div>
            <div className="mt-2 text-xs text-gray-400">Sharing insights in real-time</div>
          </div>
        </div>
      );
    
    case "TRAPPED DATA":
      return null;
    
    case "WAITING GAME":
      return null;
    
    case "EXPERTISE BARRIER":
      return null;
    
    case "SPEAK ENGLISH, NOT CODE":
      return (
        <div className="w-full h-32 bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
          <div className="p-3">
            <div className="bg-green-900/30 p-2 rounded text-xs text-green-200 font-mono">
              <div className="text-green-400">❓</div>
              <div className="ml-2">"Show me temperature trends in Pacific"</div>
              <div className="text-green-400 mt-1">✅</div>
              <div className="ml-2">No coding required</div>
            </div>
          </div>
        </div>
      );
    
    default:
      return (
        <div className="w-full h-32 bg-gray-900 rounded-lg border border-gray-700">
          <div className="p-3 flex items-center justify-center h-full text-gray-400">
            Interactive preview
          </div>
        </div>
      );
  }
};

export default function GlassCard({ title, desc }: { title: string; desc?: string }) {
  return (
    <MotionDiv
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ duration: 0.2 }}
      className="glass-card p-6 liquid-radius outline-1 shadow-figma-soft group hover:border-slate-400/20 transition-all duration-300 cursor-pointer relative overflow-hidden"
    >
      {/* Content Preview - Hide for section 3 cards */}
      <div className="mb-4">
        {title !== "SPEAK ENGLISH, NOT CODE" && title !== "SEE. DON'T GUESS" && title !== "SHARE. DON'T HOARD" && (
          <ContentPreview title={title} />
        )}
      </div>
      
      <h4 className="text-xl font-bold mb-3 text-white group-hover:text-blue-300 transition-colors duration-300">
        {title}
      </h4>
      <p className="text-sm text-slate-300 leading-relaxed group-hover:text-slate-200 transition-colors duration-300">
        {desc}
      </p>
      
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-3xl" />
      
      <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <span className="text-slate-400">→</span>
      </div>
    </MotionDiv>
  );
}

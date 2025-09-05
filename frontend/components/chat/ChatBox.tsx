"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function ChatBox({
  placeholder = "What do you want to know?",
}: {
  placeholder?: string;
}) {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleSubmit = () => {
    if (!query.trim()) return;
    router.push("/live"); // temporary redirect
  };

  return (
    <div className="relative w-full max-w-4xl mx-auto z-[9999]">
      {/* Chat input container */}
      <div
        className="flex items-center gap-4 px-6 py-6 hero-noise"
        style={{
          borderRadius: "28px",
          border: "1px solid rgba(255,255,255,0.12)",
          background: "rgba(255,255,255,0.04)",
          boxShadow:
            "0 18px 50px rgba(2,6,23,0.7), inset 0 2px 0 rgba(255,255,255,0.02)",
          backdropFilter: "blur(16px) saturate(120%)",
        }}
      >
        {/* Typable input */}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder={placeholder}
          className="flex-1 bg-transparent focus:outline-none placeholder:text-slate-400 text-white text-base md:text-lg"
        />

        {/* Send button */}
        <button
          onClick={handleSubmit}
          className="w-12 h-12 flex items-center justify-center rounded-full transition hover:scale-105"
          style={{
            background:
              "radial-gradient(circle at 30% 30%, rgba(255,255,255,0.06), rgba(255,255,255,0.01))",
            border: "1px solid rgba(255,255,255,0.15)",
            boxShadow: "0 6px 18px rgba(2,6,23,0.6)",
          }}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="white"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Outer glow border */}
      <div
        className="absolute inset-0 pointer-events-none rounded-[28px]"
        style={{
          boxShadow:
            "0 0 0 1px rgba(255,255,255,0.04) inset, 0 12px 40px rgba(2,6,23,0.5)",
          borderRadius: "28px",
        }}
      />
    </div>
  );
}

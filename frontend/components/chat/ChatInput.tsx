"use client";

import { useState, useRef, useEffect } from "react";

export default function ChatInput({ onSend }: { onSend: (text: string) => void }) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    // ensure it’s focusable / not covered
    ref.current?.focus();
  }, []);

  const submit = () => {
    const t = text.trim();
    if (!t) return;
    onSend(t);
    setText("");
  };

  return (
    <div
      className="liquid-glass liquid-radius px-4 py-4 shadow-figma-soft"
      style={{ boxShadow: "0 18px 50px rgba(2,6,23,0.55)" }}
    >
      <div className="flex items-center gap-3">
        <input
          ref={ref}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="Ask Void anything…"
          className="flex-1 bg-transparent focus:outline-none text-white placeholder:text-white/50 text-[15px]"
        />
        <button
          onClick={submit}
          aria-label="Send"
          className="w-10 h-10 rounded-full border border-white/15 hover:border-white/25 transition flex items-center justify-center"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M5 12h14M13 5l7 7-7 7" stroke="white" strokeWidth="1.4" strokeLinecap="round" />
          </svg>
        </button>
      </div>
    </div>
  );
}

"use client";

import { Suspense } from "react";
import ChatShell from "../../components/chat/ChatShell";

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen bg-black text-white">Loading...</div>}>
      <ChatShell />
    </Suspense>
  );
}

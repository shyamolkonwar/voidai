import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Chat Session - VOID',
  description: 'Chat with VOID Ocean Data Assistant',
};

export default function ChatSessionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
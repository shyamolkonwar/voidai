"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Sidebar from "./Sidebar";
import MessageList, { ChatMessage } from "./MessageList";
import ChatInput from "./ChatInput";
import Loader from "./Loader";
import { ApiClient } from "../../lib/api";
import { SessionManager } from "../../lib/session";
import { QueryResponse, SessionInfo } from "../../types/api";

/**
 * Format data for chart visualization
 */
function formatChartData(data: any[], visualizationType?: string): any[] {
  if (!data || data.length === 0) return [];

  // Try to extract numeric values for charting
  const firstRow = data[0];
  const keys = Object.keys(firstRow);

  // Find potential x and y axes
  let xKey = keys.find(key => key.toLowerCase().includes('time') || key.toLowerCase().includes('date')) || keys[0];
  let yKey = keys.find(key => key.toLowerCase().includes('value') || key.toLowerCase().includes('temp')) || keys[1];

  // If we can't find good keys, use the first two
  if (keys.length >= 2) {
    xKey = keys[0];
    yKey = keys[1];
  }

  // Format data for lightweight-charts
  return data.map(row => ({
    time: row[xKey],
    value: parseFloat(row[yKey]) || 0
  }));
}

export type Chat = {
  id: string;
  title: string;
  messages: ChatMessage[];
  message_count?: number;
  last_activity?: string;
};

function formatAssistantMessage(response: QueryResponse): ChatMessage {
  let aiResponse: ChatMessage;

  if (response.response_type === 'map' || response.visualization_type === 'map') {
    const points = response.data
      .map((d: any) => ({ lat: d.latitude, lng: d.longitude, summary: d }))
      .filter(p => p.lat != null && p.lng != null);

    const avgLat = points.reduce((sum, p) => sum + p.lat, 0) / (points.length || 1);
    const avgLng = points.reduce((sum, p) => sum + p.lng, 0) / (points.length || 1);

    aiResponse = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: response.reasoning,
      kind: "map",
      map: { 
        lat: avgLat || 20, 
        lng: avgLng || 72, 
        zoom: 2, 
        points 
      },
      timestamp: new Date().toISOString(),
      full_response: response
    };
  } else if (response.response_type === 'visualization' && response.visualization_type && response.data && response.data.length > 0) {
    // Handle chart visualizations
    aiResponse = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: response.reasoning,
      kind: "chart",
      chart: {
        type: response.visualization_type as 'line' | 'bar' | 'scatter',
        data: formatChartData(response.data, response.visualization_type),
      },
      timestamp: new Date().toISOString(),
      full_response: response
    };
  } else if (response.response_type === 'data_query' && response.data && response.data.length > 0) {
    aiResponse = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: response.reasoning,
      kind: "table",
      table: {
        columns: Object.keys(response.data[0] || {}),
        rows: response.data.map(row => Object.values(row)),
      },
      timestamp: new Date().toISOString(),
      full_response: response
    };
  } else {
    aiResponse = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: response.reasoning,
      timestamp: new Date().toISOString(),
      full_response: response
    };
  }
  return aiResponse;
}

export default function ChatShell() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const [chats, setChats] = useState<Chat[]>([]);
  
  const [currentChatId, setCurrentChatId] = useState("default-chat");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchChats = async () => {
      try {
        const response = await ApiClient.getSessions();
        if (response.sessions.length > 0) {
          const fetchedChats = response.sessions.map((session: SessionInfo) => ({
            id: session.id,
            title: session.title,
            messages: [],
            message_count: session.message_count,
            last_activity: session.last_message_at,
          }));
          setChats(fetchedChats);
          setCurrentChatId(fetchedChats[0].id);
        } else {
          handleNewChat();
        }
      } catch (err) {
        console.error("Failed to fetch chats:", err);
        setError("Failed to load chat sessions.");
      }
    };
    fetchChats();
  }, []);

  const currentChat = chats.find(chat => chat.id === currentChatId);
  const messages = currentChat?.messages || [];

  const handleSend = async (text: string) => {
    try {
      setError(null);
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        timestamp: new Date().toISOString()
      };
      
      // Add user message to current chat
      setChats(prevChats =>
        prevChats.map(chat =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, userMsg] }
            : chat
        )
      );

      // Update chat title if it's the first user message
      if (currentChat && currentChat.messages.length === 1) {
        const newTitle = text.length > 30 ? text.substring(0, 30) + "..." : text;
        setChats(prevChats =>
          prevChats.map(chat =>
            chat.id === currentChatId
              ? { ...chat, title: newTitle }
              : chat
          )
        );
      }

      // Show loading state
      setIsLoading(true);

      // Get or create session
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        currentSessionId = await SessionManager.getOrCreateSession();
        setSessionId(currentSessionId);
      }

      // Send query to backend
      const response: QueryResponse = await ApiClient.sendQuery({
        query: text,
        session_id: currentSessionId,
        include_context: true,
        max_results: 100
      });

      // Create AI response based on backend response
      let aiResponse: ChatMessage;

      if (response.response_type === 'map' || response.visualization_type === 'map') {
        const points = response.data
          .map((d: any) => ({ lat: d.latitude, lng: d.longitude, summary: d }))
          .filter(p => p.lat != null && p.lng != null);

        const avgLat = points.reduce((sum, p) => sum + p.lat, 0) / (points.length || 1);
        const avgLng = points.reduce((sum, p) => sum + p.lng, 0) / (points.length || 1);

        aiResponse = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.reasoning,
          kind: "map",
          map: { 
            lat: avgLat || 20, 
            lng: avgLng || 72, 
            zoom: 2, 
            points 
          },
          timestamp: new Date().toISOString(),
          full_response: response
        };
      } else if (response.response_type === 'visualization' && response.visualization_type && response.data && response.data.length > 0) {
        // Handle chart visualizations
        aiResponse = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.reasoning,
          kind: "chart",
          chart: {
            type: response.visualization_type as 'line' | 'bar' | 'scatter',
            data: formatChartData(response.data, response.visualization_type),
          },
          timestamp: new Date().toISOString(),
          full_response: response
        };
      } else if (response.response_type === 'data_query' && response.data && response.data.length > 0) {
        aiResponse = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.reasoning,
          kind: "table",
          table: {
            columns: Object.keys(response.data[0] || {}),
            rows: response.data.map(row => Object.values(row)),
          },
          timestamp: new Date().toISOString(),
          full_response: response
        };
      } else {
        aiResponse = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.reasoning,
          timestamp: new Date().toISOString(),
          full_response: response
        };
      }

      // Add AI response to current chat
      setChats(prevChats =>
        prevChats.map(chat =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, aiResponse] }
            : chat
        )
      );

    } catch (err) {
      console.error('Error sending message:', err);
      setError(err instanceof Error ? err.message : 'Failed to send message');
      
      // Add error message
      const errorResponse: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Sorry, I encountered an error processing your request. Please try again.",
        timestamp: new Date().toISOString()
      };
      
      setChats(prevChats =>
        prevChats.map(chat =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, errorResponse] }
            : chat
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      // Create new session for the new chat
      const newSessionId = await SessionManager.switchToNewSession();
      setSessionId(newSessionId);
      
      const newChatId = crypto.randomUUID();
      const newChat: Chat = {
        id: newChatId,
        title: "New Chat",
        messages: [
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content:
              "Hi! I'm Void — ask me anything about ARGO floats, ocean data, or run a map/table preview.",
          },
        ],
      };
      setChats(prev => [...prev, newChat]);
      setCurrentChatId(newChatId);
      
      // Update URL with session ID
      const params = new URLSearchParams(searchParams.toString());
      params.set('session', newSessionId);
      router.push(`/chat?${params.toString()}`, { scroll: false });
      
      // Force scroll after chat switch
      setTimeout(() => {
        if (messagesEndRef.current) {
          messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
        }
      }, 150);
    } catch (err) {
      console.error('Error creating new chat:', err);
      setError('Failed to create new chat session');
    }
  };

  const handleDeleteChat = (chatId: string) => {
    if (chats.length === 1) return; // Don't delete the last chat
    
    setChats(prev => prev.filter(chat => chat.id !== chatId));
    
    // If we deleted the current chat, switch to the first remaining chat
    if (chatId === currentChatId) {
      const remainingChats = chats.filter(chat => chat.id !== chatId);
      if (remainingChats.length > 0) {
        setCurrentChatId(remainingChats[0].id);
      }
    }
  };

  const handleSelectChat = (chatId: string) => {
    setCurrentChatId(chatId);
    setSessionId(chatId);
    
    // Update URL with session ID if available
    const params = new URLSearchParams(searchParams.toString());
    params.set('session', chatId);
    router.push(`/chat?${params.toString()}`, { scroll: false });
    
    // Force scroll after chat switch
    setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
      }
    }, 150);
  };

  // Initialize session on component mount and handle URL params
  useEffect(() => {
    const initializeSession = async () => {
      try {
        // Check if session ID is in URL
        const urlSessionId = searchParams.get('session');
        
        if (urlSessionId) {
          // Validate the session from URL
          const isValid = await SessionManager.validateSession(urlSessionId);
          if (isValid) {
            setSessionId(urlSessionId);
            // Use SessionManager to set the session instead of direct storage access
            await SessionManager.getOrCreateSession(); // This will set the session in storage
            return;
          }
        }
        
        // Create new session if no valid session in URL
        const session = await SessionManager.getOrCreateSession();
        setSessionId(session);
        
        // Update URL with new session ID
        const params = new URLSearchParams(searchParams.toString());
        params.set('session', session);
        router.push(`/chat?${params.toString()}`, { scroll: false });
        
      } catch (err) {
        console.error('Failed to initialize session:', err);
        setError('Failed to initialize chat session');
      }
    };
    
    initializeSession();
  }, [searchParams, router]);

  // Auto-scroll to bottom when new messages are added or chat changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (scrollContainerRef.current) {
        const container = scrollContainerRef.current;
        container.scrollTo({
          top: container.scrollHeight,
          behavior: 'smooth'
        });
      }
    }, 100);
    return () => clearTimeout(timer);
  }, [messages, isLoading, currentChatId]);

  // Load session history when session changes
  useEffect(() => {
    const loadSessionHistory = async () => {
      if (sessionId) {
        try {
          const history = await ApiClient.getSessionHistory(sessionId);
          if (history.messages && history.messages.length > 0) {
            // Convert backend messages to frontend format
            const formattedMessages: ChatMessage[] = history.messages.map((msg: ChatMessage) => {
              if (msg.role === 'assistant') {
                // Re-process full_response to get kind, map, table, chart
                return formatAssistantMessage(msg.full_response as QueryResponse);
              } else {
                return {
                  id: crypto.randomUUID(),
                  role: msg.role as 'user' | 'assistant',
                  content: msg.content || '',
                  timestamp: msg.timestamp,
                  full_response: msg.full_response
                };
              }
            });
            
            setChats(prev => prev.map(chat =>
              chat.id === currentChatId
                ? { ...chat, messages: formattedMessages }
                : chat
            ));
          }
        } catch (err) {
          console.error('Failed to load session history:', err);
        }
      }
    };
    
    loadSessionHistory();
  }, [sessionId, currentChatId]);

  return (
    <div className="fixed inset-0 h-screen w-full bg-black text-white">
      <div className="h-full grid grid-cols-[auto,1fr]">
        <Sidebar 
          chats={chats}
          currentChatId={currentChatId}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
          onDeleteChat={handleDeleteChat}
        />
        <div className="h-full flex flex-col">
          {/* top brand like ChatGPT */}
          <div className="flex-shrink-0 px-6 pt-4 pb-2 bg-black border-b border-white/5 z-10">
            <span className="text-sm font-large tracking-wide text-white/80">Void</span>
          </div>

          {/* messages container with proper scrolling */}
          <div 
            ref={scrollContainerRef}
            className="flex-1 overflow-y-auto chat-scrollbar"
            style={{ minHeight: 0, maxHeight: 'calc(100vh - 140px)' }}
          >
            <div className="w-full max-w-3xl mx-auto px-6 py-4 min-h-full">
              <MessageList messages={messages} />
              {isLoading && (
                <div className="flex items-center gap-3 mt-6 mb-4">
                  <Loader />
                  <span className="text-white/70 text-sm">AI is thinking...</span>
                </div>
              )}
              
              {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 mt-4">
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}
              {/* Invisible element to scroll to */}
              <div ref={messagesEndRef} className="h-1" />
            </div>
          </div>

          {/* input (always at bottom) */}
          <div className="flex-shrink-0 border-t border-white/5 bg-black z-10 sticky bottom-0">
            <div className="max-w-4xl mx-auto px-4 py-4">
              <ChatInput onSend={handleSend} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

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
 * Extracts chart type and plot keys from a user's query.
 * @param query The user's query string.
 * @returns An object with chartType, xKey, and yKey, or null if not found.
 */
function extractChartInfo(query: string): { chartType: string, xKey: string, yKey: string } | null {
  const lowerCaseQuery = query.toLowerCase();
  
  // Enhanced patterns to handle various query formats
  const patterns = [
    // Pattern 1: "compare pressure vs temperature in a line chart"
    /compare\s+(\w+)\s+vs\s+(\w+)\s+(?:in|with|using)\s+(?:a\s+)?(line|bar|pie|doughnut|polarArea|radar|scatter|bubble)\s+chart/i,
    
    // Pattern 2: "show me pressure vs temperature as a line chart"
    /(?:show|display|plot|graph)\s+(?:\w+\s+)*(\w+)\s+vs\s+(\w+)\s+(?:as|in)\s+(?:a\s+)?(line|bar|pie|doughnut|polarArea|radar|scatter|bubble)\s+chart/i,
    
    // Pattern 3: "line chart of pressure vs temperature"
    /(line|bar|pie|doughnut|polarArea|radar|scatter|bubble)\s+chart\s+(?:of|for)\s+(\w+)\s+vs\s+(\w+)/i,
    
    // Pattern 4: "plot pressure vs temperature"
    /(?:plot|graph|show|display)\s+(\w+)\s+vs\s+(\w+)/i,
    
    // Pattern 5: "compare pressure and temperature"
    /compare\s+(\w+)\s+and\s+(\w+)/i,
    
    // Pattern 6: "pressure vs temperature chart"
    /(\w+)\s+vs\s+(\w+)\s+chart/i,
  ];

  for (const pattern of patterns) {
    const match = lowerCaseQuery.match(pattern);
    if (match) {
      if (match.length === 4) {
        // Patterns 1, 2, 3: chartType, xKey, yKey
        return { chartType: match[3], xKey: match[1], yKey: match[2] };
      } else if (match.length === 3) {
        // Patterns 4, 5, 6: xKey, yKey (default to line chart)
        return { chartType: 'line', xKey: match[1], yKey: match[2] };
      }
    }
  }

  // Fallback: look for "vs" pattern anywhere in the query
  const vsMatch = lowerCaseQuery.match(/(\w+)\s+vs\s+(\w+)/);
  if (vsMatch) {
    const chartTypeMatch = lowerCaseQuery.match(/(line|bar|pie|doughnut|polarArea|radar|scatter|bubble)/);
    return {
      chartType: chartTypeMatch ? chartTypeMatch[1] : 'line',
      xKey: vsMatch[1],
      yKey: vsMatch[2]
    };
  }

  // Fallback: look for "and" pattern for comparisons
  const andMatch = lowerCaseQuery.match(/(\w+)\s+and\s+(\w+)/);
  if (andMatch && (lowerCaseQuery.includes('compare') || lowerCaseQuery.includes('chart'))) {
    const chartTypeMatch = lowerCaseQuery.match(/(line|bar|pie|doughnut|polarArea|radar|scatter|bubble)/);
    return {
      chartType: chartTypeMatch ? chartTypeMatch[1] : 'line',
      xKey: andMatch[1],
      yKey: andMatch[2]
    };
  }

  return null;
}

/**
 * Format data for chart visualization with enhanced trading data support
 */
function formatChartData(data: any[], xKey?: string, yKey?: string): any[] {
  if (!data || data.length === 0) return [];

  const firstRow = data[0];
  const keys = Object.keys(firstRow);

  const findKey = (keyName?: string) => {
      if (!keyName) return undefined;
      const lowerKeyName = keyName.toLowerCase();
      
      // First try exact match
      const exactMatch = keys.find(k => k.toLowerCase() === lowerKeyName);
      if (exactMatch) return exactMatch;
      
      // Then try contains match
      const containsMatch = keys.find(k => k.toLowerCase().includes(lowerKeyName));
      if (containsMatch) return containsMatch;
      
      // Try common synonyms and variations
      const synonyms: Record<string, string[]> = {
        'temperature': ['temp', 't', 'degrees', 'celsius', 'fahrenheit'],
        'pressure': ['press', 'p', 'hpa', 'mb', 'millibar'],
        'salinity': ['salt', 's', 'psu', 'practical salinity'],
        'depth': ['d', 'm', 'meters', 'metres'],
        'time': ['date', 'timestamp', 'datetime', 'hour', 'minute', 'second'],
        'latitude': ['lat', 'y'],
        'longitude': ['lon', 'long', 'lng', 'x']
      };
      
      if (synonyms[lowerKeyName]) {
        for (const synonym of synonyms[lowerKeyName]) {
          const synonymMatch = keys.find(k => k.toLowerCase().includes(synonym));
          if (synonymMatch) return synonymMatch;
        }
      }
      
      // Try reverse lookup - if keyName is a synonym, find the main key
      for (const [mainKey, synonymList] of Object.entries(synonyms)) {
        if (synonymList.includes(lowerKeyName)) {
          const mainKeyMatch = keys.find(k => k.toLowerCase().includes(mainKey));
          if (mainKeyMatch) return mainKeyMatch;
        }
      }
      
      return undefined;
  }

  let finalXKey = findKey(xKey);
  let finalYKey = findKey(yKey);

  // Try to find suitable keys for charting
  if (!finalXKey || !finalYKey) {
    const numericKeys = keys.filter(key =>
      typeof firstRow[key] === 'number' ||
      !isNaN(parseFloat(firstRow[key]))
    );
    
    const stringKeys = keys.filter(key =>
      typeof firstRow[key] === 'string' &&
      !numericKeys.includes(key)
    );

    // Try to find a time/date column for x-axis
    const timePatterns = ['time', 'date', 'timestamp', 'year', 'month', 'day'];
    const timeKey = keys.find(key =>
      timePatterns.some(pattern => key.toLowerCase().includes(pattern))
    );

    if (numericKeys.length >= 1) {
      // Use time key for x-axis if available, otherwise use first numeric key
      finalXKey = finalXKey || timeKey || (numericKeys.length > 1 ? numericKeys[0] : stringKeys[0] || keys[0]);
      finalYKey = finalYKey || (numericKeys.find(k => k !== finalXKey) || numericKeys[0]);
    } else if (keys.length >= 2) {
      // Fallback: use first two columns
      finalXKey = finalXKey || keys[0];
      finalYKey = finalYKey || keys[1];
    }
  }

  if (!finalXKey || !finalYKey) {
    return []; // Not enough data to plot
  }

  const formattedData = data.map((row, index) => {
    let xValue = row[finalXKey!];
    let yValue = row[finalYKey!];

    // Handle date/time values for the x-axis
    if (typeof xValue === 'string') {
      const date = new Date(xValue);
      if (!isNaN(date.getTime())) {
        xValue = date.getTime() / 1000;
      }
    }

    // Convert y-value to number if possible
    if (typeof yValue === 'string' && !isNaN(parseFloat(yValue))) {
      yValue = parseFloat(yValue);
    }

    return {
      time: xValue,
      value: yValue
    };
  });

  const uniqueData = formattedData.filter((item, index, self) =>
    index === self.findIndex(t => t.time === item.time)
  );
  
  const sortedData = uniqueData.sort((a, b) => {
    if (typeof a.time === 'number' && typeof b.time === 'number') {
      return a.time - b.time;
    }
    if (typeof a.time === 'string' && typeof b.time === 'string') {
      return a.time.localeCompare(b.time);
    }
    return 0;
  });
  
  return sortedData;
}

export type Chat = {
  id: string;
  title: string;
  messages: ChatMessage[];
  message_count?: number;
  last_activity?: string;
};

function formatAssistantMessage(response: QueryResponse, query: string): ChatMessage {
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
  } else if (response.response_type === 'visualization' && response.data && response.data.length > 0) {
    const chartInfo = extractChartInfo(query);
    const chartData = formatChartData(response.data, chartInfo?.xKey, chartInfo?.yKey);
    const chartType = chartInfo?.chartType || response.visualization_type || 'line';

    // Always show chart for visualization intent, even with minimal data
    if (chartData && chartData.length >= 1) {
      aiResponse = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.reasoning,
        kind: "chart",
        chart: {
          type: chartType as any,
          data: chartData,
        },
        timestamp: new Date().toISOString(),
        full_response: response
      };
    } else {
      // If we can't format chart data, show a simple message with the data
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
    }
  } else if (response.response_type === 'data_query' && response.data && response.data.length > 0) {
    // Check if visualization is requested even for data queries
    const chartInfo = extractChartInfo(query);
    const shouldVisualize = response.visualization_type || chartInfo;
    
    if (shouldVisualize && response.data.length > 0) {
      const chartData = formatChartData(response.data, chartInfo?.xKey, chartInfo?.yKey);
      const chartType = chartInfo?.chartType || response.visualization_type || 'line';

      if (chartData && chartData.length > 1) {
        aiResponse = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: response.reasoning,
          kind: "chart",
          chart: {
            type: chartType as any,
            data: chartData,
          },
          timestamp: new Date().toISOString(),
          full_response: response
        };
      } else {
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
      }
    } else {
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
    }
  } else if ((response.response_type === 'conversational' || response.response_type === 'help') && response.data && response.data.length > 0) {
    const messageContent = response.data[0]?.message || response.reasoning;
    aiResponse = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: messageContent,
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
      
      setChats(prevChats =>
        prevChats.map(chat =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, userMsg] }
            : chat
        )
      );

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

      setIsLoading(true);

      let currentSessionId = sessionId;
      if (!currentSessionId) {
        currentSessionId = await SessionManager.getOrCreateSession();
        setSessionId(currentSessionId);
      }

      const response: QueryResponse = await ApiClient.sendQuery({
        query: text,
        session_id: currentSessionId,
        include_context: true,
        max_results: 100
      });

      const aiResponse = formatAssistantMessage(response, text);

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
              "Hi! I'm Void — ask me anything!",
          },
        ],
      };
      setChats(prev => [...prev, newChat]);
      setCurrentChatId(newChatId);
      
      const params = new URLSearchParams(searchParams.toString());
      params.set('session', newSessionId);
      router.push(`/chat?${params.toString()}`, { scroll: false });
      
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
    if (chats.length === 1) return;
    
    setChats(prev => prev.filter(chat => chat.id !== chatId));
    
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
    
    const params = new URLSearchParams(searchParams.toString());
    params.set('session', chatId);
    router.push(`/chat?${params.toString()}`, { scroll: false });
    
    setTimeout(() => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
      }
    }, 150);
  };

  useEffect(() => {
    const initializeSession = async () => {
      try {
        const urlSessionId = searchParams.get('session');
        
        if (urlSessionId) {
          const isValid = await SessionManager.validateSession(urlSessionId);
          if (isValid) {
            setSessionId(urlSessionId);
            await SessionManager.getOrCreateSession();
            return;
          }
        }
        
        const session = await SessionManager.getOrCreateSession();
        setSessionId(session);
        
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

  useEffect(() => {
    const loadSessionHistory = async () => {
      if (sessionId) {
        try {
          const history = await ApiClient.getSessionHistory(sessionId);
          if (history.messages && history.messages.length > 0) {
            const formattedMessages: ChatMessage[] = history.messages.map((msg: ChatMessage, index: number) => {
              if (msg.role === 'assistant') {
                const userQuery = history.messages[index - 1]?.content || '';
                return formatAssistantMessage(msg.full_response as QueryResponse, userQuery);
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
          <div className="flex-shrink-0 px-6 pt-4 pb-2 bg-black border-b border-white/5 z-10">
            <span className="text-sm font-large tracking-wide text-white/80">Void</span>
          </div>

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
              <div ref={messagesEndRef} className="h-1" />
            </div>
          </div>

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
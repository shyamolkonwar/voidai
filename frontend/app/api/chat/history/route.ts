import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    // Get session ID from query parameters
    const { searchParams } = new URL(request.url);
    const sessionId = searchParams.get('sessionId');
    
    if (!sessionId) {
      return NextResponse.json(
        { error: 'Session ID is required' },
        { status: 400 }
      );
    }
    
    // Forward the request to the backend
    const backendUrl = `http://127.0.0.1:8001/api/v1/sessions/${sessionId}/history`;
    const backendResponse = await fetch(backendUrl);

    if (!backendResponse.ok) {
      throw new Error(`Backend error: ${backendResponse.status}`);
    }

    const responseData = await backendResponse.json();
    
    // Convert backend messages to frontend format with full response data
    const messages = responseData.messages.map((msg: any) => {
      const messageObj: any = {
        id: msg.id || `${msg.role}-${Date.now()}-${Math.random()}`,
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.timestamp || Date.now()),
      };
      
      // For assistant messages, include the full response data for smart context awareness
      if (msg.role === 'assistant' && msg.full_response) {
        messageObj.response = {
          type: msg.full_response.type || 'text',
          data: msg.full_response.data || [],
          summary: msg.full_response.summary || msg.full_response.reasoning || 'No summary available',
          // Include additional response metadata
          sql_query: msg.full_response.sql_query,
          row_count: msg.full_response.row_count,
          confidence_score: msg.full_response.confidence_score,
          execution_time: msg.full_response.execution_time,
          reasoning: msg.full_response.reasoning,
          success: msg.full_response.success,
          // Store the complete response data for future context retrieval
          full_response: msg.full_response
        };
      } else if (msg.response) {
        // Preserve existing response format for backward compatibility
        messageObj.response = msg.response;
      }
      
      return messageObj;
    });

    // Return the messages array
    return NextResponse.json({
      messages,
      sessionId
    });
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch chat history' },
      { status: 500 }
    );
  }
}
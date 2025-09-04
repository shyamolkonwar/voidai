import { NextRequest, NextResponse } from 'next/server';
import { v4 as uuidv4 } from 'uuid';

export async function POST(request: NextRequest) {
  try {
    const { query, sessionId } = await request.json();
    
    // Forward the request to the backend
    const backendUrl = 'http://127.0.0.1:8001/query';
    const backendResponse = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        session_id: sessionId,
      }),
    });

    if (!backendResponse.ok) {
      throw new Error(`Backend error: ${backendResponse.status}`);
    }

    const responseData = await backendResponse.json();
    
    // Create assistant message from the response with full response data
    const assistantMessage = {
      id: `assistant-${uuidv4()}`,
      role: 'assistant',
      content: responseData.summary || 'No response available',
      timestamp: new Date(),
      response: {
        type: responseData.type || 'text',
        data: responseData.data || [],
        summary: responseData.summary || responseData.reasoning || 'No summary available',
        // Include additional response metadata for smart context awareness
        sql_query: responseData.sql_query,
        row_count: responseData.row_count,
        confidence_score: responseData.confidence_score,
        execution_time: responseData.execution_time,
        reasoning: responseData.reasoning,
        success: responseData.success,
        // Store the complete response data for future context retrieval
        full_response: responseData
      },
    };

    // Return the messages array with the new assistant message
    return NextResponse.json({
      messages: [assistantMessage],
      sessionId
    });
  } catch (error) {
    console.error('API route error:', error);
    return NextResponse.json(
      { error: 'Failed to process chat request' },
      { status: 500 }
    );
  }
}
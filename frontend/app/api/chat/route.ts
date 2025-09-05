import { NextRequest, NextResponse } from 'next/server';
import { QueryRequest, QueryResponse, ApiError } from '../../../types/api';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

export async function POST(request: NextRequest) {
  try {
    const body: QueryRequest = await request.json();
    
    // Validate request
    if (!body.query || body.query.trim().length === 0) {
      return NextResponse.json(
        { error: 'Validation Error', message: 'Query is required', statusCode: 400 },
        { status: 400 }
      );
    }

    // Forward request to backend
    const response = await fetch(`${BACKEND_URL}/api/v1/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { 
          error: 'Backend Error', 
          message: errorData.detail || 'Failed to process query', 
          statusCode: response.status 
        },
        { status: response.status }
      );
    }

    const data: QueryResponse = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error in chat API:', error);
    return NextResponse.json(
      { error: 'Internal Server Error', message: 'Failed to process request', statusCode: 500 },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json(
    { error: 'Method Not Allowed', message: 'Use POST method for chat queries', statusCode: 405 },
    { status: 405 }
  );
}
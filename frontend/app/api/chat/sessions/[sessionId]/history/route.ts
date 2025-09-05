import { NextRequest, NextResponse } from 'next/server';
import { SessionHistoryResponse, ApiError } from '../../../../../../types/api';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001';

export async function GET(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const pathname = request.nextUrl.pathname;
    const parts = pathname.split('/');
    const sessionId = parts[4];

    if (!sessionId) {
      return NextResponse.json(
        { error: 'Validation Error', message: 'Session ID is required', statusCode: 400 },
        { status: 400 }
      );
    }

    // Get session history from backend
    const response = await fetch(`${BACKEND_URL}/api/v1/sessions/${sessionId}/history`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return NextResponse.json(
        { 
          error: 'Backend Error', 
          message: errorData.detail || 'Failed to fetch session history', 
          statusCode: response.status 
        },
        { status: response.status }
      );
    }

    const data: SessionHistoryResponse = await response.json();
    return NextResponse.json(data);

  } catch (error) {
    console.error('Error fetching session history:', error);
    return NextResponse.json(
      { error: 'Internal Server Error', message: 'Failed to fetch session history', statusCode: 500 },
      { status: 500 }
    );
  }
}
import { NextResponse } from 'next/server';

const API_URL = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    const res = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    
    if (!res.ok) {
        return NextResponse.json(data, { status: res.status });
    }
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in chat proxy:', error);
    return NextResponse.json(
      { error: 'Failed to proxy chat request' },
      { status: 500 }
    );
  }
}

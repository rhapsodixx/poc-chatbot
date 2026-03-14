import { NextResponse } from 'next/server';

const API_URL = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const res = await fetch(`${API_URL}/api/ingest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error triggering ingestion:', error);
    return NextResponse.json(
      { error: 'Failed to trigger ingestion' },
      { status: 500 }
    );
  }
}

import { NextResponse } from 'next/server';

const API_URL = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET() {
  try {
    const res = await fetch(`${API_URL}/api/ingest/status`, {
      method: 'GET',
    });

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching ingestion status:', error);
    return NextResponse.json(
      { error: 'Failed to fetch ingestion status' },
      { status: 500 }
    );
  }
}

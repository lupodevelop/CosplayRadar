import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');

    // Test diretto con fetch invece di axios per evitare problemi di import
    const response = await fetch(`https://api.jikan.moe/v4/top/characters?page=${page}`, {
      method: 'GET',
      headers: {
        'User-Agent': 'CosplayRadar/1.0',
      },
    });

    if (!response.ok) {
      throw new Error(`Jikan API responded with status: ${response.status}`);
    }

    const data = await response.json();

    return NextResponse.json({
      success: true,
      characters: data.data?.slice(0, 5).map((char: any) => ({
        id: char.mal_id,
        name: char.name,
        favorites: char.favorites,
        imageUrl: char.images?.jpg?.image_url,
      })) || [],
      pagination: data.pagination,
      source: 'jikan-direct',
    });
  } catch (error) {
    console.error('Jikan API error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to fetch characters',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Test diretto dell'API Jikan per anime attualmente in onda
    const response = await fetch('https://api.jikan.moe/v4/top/anime?filter=airing&limit=5');
    const data = await response.json();
    
    return NextResponse.json({
      message: 'Current airing anime test',
      count: data.data?.length || 0,
      anime: data.data?.map((anime: any) => ({
        title: anime.title,
        year: anime.year,
        season: anime.season,
        popularity: anime.popularity,
        members: anime.members,
        status: anime.status,
        mal_id: anime.mal_id,
      })) || []
    });
  } catch (error) {
    return NextResponse.json({ 
      error: 'Failed to fetch airing anime',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

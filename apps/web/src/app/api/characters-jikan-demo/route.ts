/**
 * Route demo per mostrare i personaggi da Jikan API direttamente
 */

import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');

    console.log(`Fetching characters from Jikan API page ${page}...`);
    
    const response = await fetch(`https://api.jikan.moe/v4/top/characters?page=${page}`, {
      method: 'GET',
      headers: {
        'User-Agent': 'CosplayRadar/1.0',
      },
    });

    if (!response.ok) {
      throw new Error(`Jikan API responded with status: ${response.status}`);
    }

    const jikanData = await response.json();
    
    // Converte i personaggi Jikan nel formato API
    const jikanCharacters = jikanData.data.map((character: any) => ({
      id: character.mal_id.toString(),
      name: character.name,
      series: character.anime?.[0]?.anime?.title || character.manga?.[0]?.manga?.title || 'MyAnimeList',
      category: character.anime?.length > 0 ? 'ANIME' : character.manga?.length > 0 ? 'MANGA' : 'OTHER',
      difficulty: Math.min(Math.ceil((character.favorites || 0) / 20000), 5) || 1,
      popularity: character.favorites || 0,
      imageUrl: character.images?.jpg?.image_url || null,
      description: character.about?.substring(0, 200) || `Popular character with ${character.favorites} favorites on MyAnimeList`,
      tags: character.nicknames || [],
      trendingScore: Math.min((character.favorites || 0) / 1000, 200), // Trending score più visibile
      socialLinks: {
        reddit: `https://reddit.com/search?q=${encodeURIComponent(character.name)}`,
        twitter: `https://twitter.com/search?q=${encodeURIComponent(character.name)}`,
        instagram: `https://instagram.com/explore/tags/${encodeURIComponent(character.name.replace(/\s+/g, ""))}`,
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      isFromJikan: true,
    }));

    return NextResponse.json({
      characters: jikanCharacters,
      pagination: {
        page: jikanData.pagination.current_page,
        limit: 25,
        totalCount: jikanData.pagination.items.total,
        totalPages: jikanData.pagination.last_visible_page,
        hasNext: jikanData.pagination.has_next_page,
        hasPrev: page > 1,
      },
      filters: {
        category: null,
        difficulty: null,
        search: null,
        sortBy: 'popularity',
      },
      source: 'jikan-demo',
      message: 'Live data from MyAnimeList via Jikan API',
    });
  } catch (error) {
    console.error('Jikan demo API error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to fetch characters from Jikan',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

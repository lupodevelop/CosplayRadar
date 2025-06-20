/**
 * Test route per forzare l'uso di Jikan API
 */

import { NextRequest, NextResponse } from 'next/server';
import { jikanService } from '@/services/jikanService';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');

    console.log(`Testing Jikan API with page ${page}...`);
    
    const jikanResult = await jikanService.getTopCharacters({ page });
    
    // Converte i personaggi Jikan nel formato API
    const jikanCharacters = jikanResult.characters.map(character => ({
      id: character.id,
      name: character.name,
      series: character.series,
      category: character.category,
      difficulty: Math.min(Math.ceil(character.favorites / 5000), 5),
      popularity: character.popularity,
      imageUrl: character.imageUrl,
      description: character.description,
      tags: character.tags,
      trendingScore: character.popularityScore,
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
        page: jikanResult.pagination.currentPage,
        limit: 25,
        totalCount: jikanResult.pagination.totalPages * 25,
        totalPages: jikanResult.pagination.totalPages,
        hasNext: jikanResult.pagination.hasNextPage,
        hasPrev: page > 1,
      },
      source: 'jikan',
      message: 'Data from Jikan API',
    });
  } catch (error) {
    console.error('Jikan test API error:', error);
    
    return NextResponse.json(
      { 
        error: 'Failed to fetch from Jikan', 
        message: error instanceof Error ? error.message : 'Unknown error',
        source: 'jikan-error'
      },
      { status: 500 }
    );
  }
}

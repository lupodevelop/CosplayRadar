import { NextRequest, NextResponse } from 'next/server';
import { anilistService } from '@/services/anilistService';

export async function GET(request: NextRequest) {
  try {
    console.log('Testing AniList service directly...');
    
    // Test getTopCharacters direttamente con l'istanza
    const result = await anilistService.getTopCharacters({
      page: 1,
      perPage: 5,
    });
    
    console.log('AniList service test successful');
    console.log(`Fetched ${result.characters.length} characters`);
    
    return NextResponse.json({
      success: true,
      message: 'AniList service working correctly',
      charactersCount: result.characters.length,
      firstCharacter: result.characters[0] ? {
        name: result.characters[0].name,
        series: result.characters[0].series,
        gender: result.characters[0].gender,
        favorites: result.characters[0].favorites,
      } : null,
      pagination: result.pagination,
    });
    
  } catch (error) {
    console.error('AniList service test failed:', error);
    
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
    }, { status: 500 });
  }
}

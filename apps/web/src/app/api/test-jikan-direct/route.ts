import { NextRequest, NextResponse } from 'next/server';
import { jikanService } from '@/services/jikanService';

export async function GET(request: NextRequest) {
  try {
    console.log('Testing Jikan service directly...');
    
    // Test getTopCharacters
    const result = await jikanService.getTopCharacters({ page: 1 });
    
    console.log('Jikan service test successful');
    console.log(`Fetched ${result.characters.length} characters`);
    
    return NextResponse.json({
      success: true,
      message: 'Jikan service working correctly',
      charactersCount: result.characters.length,
      firstCharacter: result.characters[0] ? {
        name: result.characters[0].name,
        series: result.characters[0].series,
        popularity: result.characters[0].popularity,
      } : null,
      pagination: result.pagination,
    });
    
  } catch (error) {
    console.error('Jikan service test failed:', error);
    
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
    }, { status: 500 });
  }
}

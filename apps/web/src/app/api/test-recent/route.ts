import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Test diretto dell'API per anime recenti
    const testSeasons = [
      { year: 2024, season: 'fall' },
      { year: 2024, season: 'summer' }
    ];
    
    const results = [];
    
    for (const { year, season } of testSeasons) {
      const response = await fetch(`https://api.jikan.moe/v4/seasons/${year}/${season}?limit=3`);
      const data = await response.json();
      
      if (data.data) {
        results.push({
          season: `${season} ${year}`,
          count: data.data.length,
          anime: data.data.map((anime: any) => ({
            title: anime.title,
            mal_id: anime.mal_id,
            members: anime.members,
            popularity: anime.popularity,
          }))
        });
      }
      
      // Delay per rate limiting
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    return NextResponse.json({
      message: 'Recent seasons test',
      results
    });
  } catch (error) {
    return NextResponse.json({ 
      error: 'Failed to fetch recent seasons',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

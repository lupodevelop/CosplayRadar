import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@cosplayradar/db';
import { simpleGoogleTrendsDbService } from '@/services/simpleGoogleTrendsDbService';

export async function POST(request: NextRequest) {
  try {
    const { action, count = 10 } = await request.json();

    if (action === 'populate-test-data') {
      // Ottieni alcuni personaggi casuali
      const characters = await prisma.character.findMany({
        select: {
          id: true,
          name: true,
          series: true,
          difficulty: true
        },
        take: count,
        orderBy: {
          popularityScore: 'desc'
        }
      });

      let populated = 0;
      const errors: string[] = [];

      for (const character of characters) {
        try {
          // Genera dati di test realistici
          const testTrends = [
            {
              characterId: character.id,
              keyword: `${character.name} cosplay`,
              keywordType: 'COSPLAY',
              region: 'GLOBAL',
              trend7d: Math.floor(Math.random() * 80) + 10, // 10-90
              trend30d: Math.floor(Math.random() * 70) + 15, // 15-85
              confidence: 0.6 + Math.random() * 0.3, // 0.6-0.9
              date: new Date().toISOString()
            },
            {
              characterId: character.id,
              keyword: character.name,
              keywordType: 'CHARACTER',
              region: 'GLOBAL',
              trend7d: Math.floor(Math.random() * 90) + 20, // 20-110
              trend30d: Math.floor(Math.random() * 85) + 25, // 25-110
              confidence: 0.7 + Math.random() * 0.2, // 0.7-0.9
              date: new Date().toISOString()
            }
          ];

          await simpleGoogleTrendsDbService.saveTrendData(character.id, testTrends);
          populated++;

        } catch (error) {
          console.error(`Error populating test data for ${character.name}:`, error);
          errors.push(`Failed for ${character.name}: ${error}`);
        }
      }

      return NextResponse.json({
        success: true,
        populated,
        totalCharacters: characters.length,
        errors,
        message: `Populated test trend data for ${populated} characters`
      });
    }

    if (action === 'clear-test-data') {
      const cleared = await simpleGoogleTrendsDbService.cleanOldTrendData(0); // Pulisci tutto
      return NextResponse.json({
        success: true,
        cleared,
        message: `Cleared ${cleared} trend data records`
      });
    }

    return NextResponse.json(
      { error: 'Invalid action. Use: populate-test-data, clear-test-data' },
      { status: 400 }
    );

  } catch (error) {
    console.error('Test data API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const stats = await simpleGoogleTrendsDbService.getTrendStats();
    const topTrends = await simpleGoogleTrendsDbService.getTopTrends(5);

    return NextResponse.json({
      success: true,
      stats,
      sampleTrends: topTrends,
      message: 'Test data status'
    });

  } catch (error) {
    console.error('Test data status error:', error);
    return NextResponse.json(
      { error: 'Failed to get test data status' },
      { status: 500 }
    );
  }
}

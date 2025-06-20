import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@cosplayradar/db';
import { simpleGoogleTrendsService } from '@/services/simpleGoogleTrendsService';
import { simpleGoogleTrendsDbService } from '@/services/simpleGoogleTrendsDbService';

export async function POST(request: NextRequest) {
  try {
    const { action, characterIds, limit = 10 } = await request.json();

    switch (action) {
      case 'update-all':
        // Aggiorna i Google Trends per tutti i personaggi
        return await updateAllCharacterTrends();

      case 'update-batch':
        // Aggiorna i Google Trends per un batch specifico di personaggi
        if (!characterIds || !Array.isArray(characterIds)) {
          return NextResponse.json(
            { error: 'characterIds array is required for batch update' },
            { status: 400 }
          );
        }
        return await updateBatchCharacterTrends(characterIds);

      case 'update-recent':
        // Aggiorna solo i personaggi più popolari/recenti
        return await updateRecentCharacterTrends(limit);

      case 'status':
        // Stato del sistema Google Trends
        return await getTrendsStatus();

      case 'clean':
        // Pulisci i dati vecchi
        return await cleanOldTrends();

      default:
        return NextResponse.json(
          { error: 'Invalid action. Use: update-all, update-batch, update-recent, status, clean' },
          { status: 400 }
        );
    }
  } catch (error) {
    console.error('Google Trends API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    return await getTrendsStatus();
  } catch (error) {
    console.error('Google Trends status error:', error);
    return NextResponse.json(
      { error: 'Failed to get trends status' },
      { status: 500 }
    );
  }
}

// Aggiorna tutti i personaggi
async function updateAllCharacterTrends() {
  try {
    console.log('Starting Google Trends update for all characters...');
    
    const characters = await prisma.character.findMany({
      select: {
        id: true,
        name: true,
        series: true,
        category: true
      }
    });

    console.log(`Found ${characters.length} characters to update trends for`);

    let updatedCount = 0;
    let errorCount = 0;
    const errors: string[] = [];

    // Processa i personaggi in batch piccoli per rispettare i rate limit
    const batchSize = 3; // Ridotto per Google Trends
    for (let i = 0; i < characters.length; i += batchSize) {
      const batch = characters.slice(i, i + batchSize);
      
      console.log(`Processing batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(characters.length / batchSize)}`);
      
      try {
        // Ottieni i trend data per questo batch di personaggi
        const trendsData = await simpleGoogleTrendsService.getTrendsForMultipleCharacters(
          batch.map(char => ({
            id: char.id,
            name: char.name,
            series: char.series || 'Unknown'
          }))
        );

        // Salva i trend data nel database usando il batch service
        const saveResult = await simpleGoogleTrendsDbService.batchSaveTrendData(trendsData);
        updatedCount += saveResult.saved;
        errors.push(...saveResult.errors);

        // Pausa più lunga tra i batch per Google Trends
        if (i + batchSize < characters.length) {
          console.log('Waiting 5 minutes before next batch...');
          await new Promise(resolve => setTimeout(resolve, 300000)); // 5 minuti
        }

      } catch (error) {
        console.error(`Error processing batch ${Math.floor(i / batchSize) + 1}:`, error);
        errors.push(`Failed to process batch ${Math.floor(i / batchSize) + 1}: ${error}`);
        errorCount += batch.length;
      }
    }

    return NextResponse.json({
      success: errorCount < characters.length / 2,
      updatedCount,
      errorCount,
      totalCharacters: characters.length,
      errors
    });

  } catch (error) {
    console.error('Google Trends update failed:', error);
    return NextResponse.json({
      success: false,
      updatedCount: 0,
      errorCount: 0,
      totalCharacters: 0,
      errors: [`Google Trends update failed: ${error}`]
    }, { status: 500 });
  }
}

// Aggiorna un batch specifico di personaggi
async function updateBatchCharacterTrends(characterIds: string[]) {
  try {
    console.log(`Starting Google Trends update for ${characterIds.length} specific characters...`);
    
    const characters = await prisma.character.findMany({
      where: {
        id: { in: characterIds }
      },
      select: {
        id: true,
        name: true,
        series: true,
        category: true
      }
    });

    console.log(`Found ${characters.length} characters to update trends for`);

    let updatedCount = 0;
    let errorCount = 0;
    const errors: string[] = [];

    // Processa tutti i personaggi richiesti
    const trendsData = await simpleGoogleTrendsService.getTrendsForMultipleCharacters(
      characters.map(char => ({
        id: char.id,
        name: char.name,
        series: char.series || 'Unknown'
      }))
    );

    // Salva i trend data nel database usando il batch service
    const saveResult = await simpleGoogleTrendsDbService.batchSaveTrendData(trendsData);
    updatedCount = saveResult.saved;
    errors.push(...saveResult.errors);

    return NextResponse.json({
      success: errorCount === 0,
      updatedCount,
      errorCount,
      totalCharacters: characters.length,
      errors
    });

  } catch (error) {
    console.error('Batch Google Trends update failed:', error);
    return NextResponse.json({
      success: false,
      updatedCount: 0,
      errorCount: 0,
      totalCharacters: 0,
      errors: [`Batch Google Trends update failed: ${error}`]
    }, { status: 500 });
  }
}

// Aggiorna solo i personaggi più popolari/recenti
async function updateRecentCharacterTrends(limit: number) {
  try {
    console.log(`Starting Google Trends update for top ${limit} popular characters...`);
    
    const characters = await prisma.character.findMany({
      select: {
        id: true,
        name: true,
        series: true,
        category: true
      },
      orderBy: [
        { popularityScore: 'desc' },
        { updatedAt: 'desc' }
      ],
      take: limit
    });

    console.log(`Found ${characters.length} characters to update trends for`);

    let updatedCount = 0;
    let errorCount = 0;
    const errors: string[] = [];

    // Processa i personaggi più popolari
    const trendsData = await simpleGoogleTrendsService.getTrendsForMultipleCharacters(
      characters.map(char => ({
        id: char.id,
        name: char.name,
        series: char.series || 'Unknown'
      }))
    );

    // Salva i trend data nel database usando il batch service
    const saveResult = await simpleGoogleTrendsDbService.batchSaveTrendData(trendsData);
    updatedCount = saveResult.saved;
    errors.push(...saveResult.errors);

    return NextResponse.json({
      success: errorCount === 0,
      updatedCount,
      errorCount,
      totalCharacters: characters.length,
      errors
    });

  } catch (error) {
    console.error('Recent Google Trends update failed:', error);
    return NextResponse.json({
      success: false,
      updatedCount: 0,
      errorCount: 0,
      totalCharacters: 0,
      errors: [`Recent Google Trends update failed: ${error}`]
    }, { status: 500 });
  }
}

// Stato del sistema trends
async function getTrendsStatus() {
  try {
    const totalCharacters = await prisma.character.count();
    const stats = await simpleGoogleTrendsDbService.getTrendStats();

    return NextResponse.json({
      status: { isRunning: false },
      stats: {
        totalCharacters,
        ...stats,
        lastUpdateDate: new Date().toISOString(),
      },
      message: 'Google Trends service status',
    });

  } catch (error) {
    console.error('Failed to get trends status:', error);
    return NextResponse.json(
      { error: 'Failed to get trends status' },
      { status: 500 }
    );
  }
}

// Pulisci i dati vecchi
async function cleanOldTrends() {
  try {
    const cleanedCount = await simpleGoogleTrendsDbService.cleanOldTrendData(30);
    return NextResponse.json({ cleanedCount });

  } catch (error) {
    console.error('Cleanup failed:', error);
    return NextResponse.json(
      { error: 'Cleanup failed' },
      { status: 500 }
    );
  }
}

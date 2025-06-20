import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@cosplayradar/db';
import { CharacterSyncService } from '@/services/characterSyncService';
import { simpleGoogleTrendsService } from '@/services/simpleGoogleTrendsService';
import { simpleGoogleTrendsDbService } from '@/services/simpleGoogleTrendsDbService';

// Funzione per sincronizzare i personaggi da Jikan
async function syncCharactersFromJikan() {
  try {
    console.log('Starting sync from Jikan...');
    
    const response = await fetch('https://api.jikan.moe/v4/top/characters?page=1', {
      method: 'GET',
      headers: {
        'User-Agent': 'CosplayRadar/1.0',
      },
    });

    if (!response.ok) {
      throw new Error(`Jikan API responded with status: ${response.status}`);
    }

    const data = await response.json();
    let syncedCount = 0;
    let updatedCount = 0;
    const errors: string[] = [];

    for (const jikanChar of data.data.slice(0, 10)) { // Sync primi 10
      try {
        // Estrai la serie principale
        let series = 'Unknown';
        if (jikanChar.anime && jikanChar.anime.length > 0) {
          series = jikanChar.anime[0].anime.title;
        } else if (jikanChar.manga && jikanChar.manga.length > 0) {
          series = jikanChar.manga[0].manga.title;
        }

        const characterData = {
          name: jikanChar.name || 'Unknown Character',
          series,
          category: (jikanChar.anime?.length > 0 ? 'ANIME' : jikanChar.manga?.length > 0 ? 'MANGA' : 'OTHER') as 'ANIME' | 'MANGA' | 'OTHER',
          difficulty: Math.min(Math.ceil((jikanChar.favorites || 0) / 20000), 5) || 1,
          popularity: parseFloat((jikanChar.favorites || 0).toString()),
          imageUrl: jikanChar.images?.jpg?.image_url || null,
          description: jikanChar.about?.substring(0, 500) || null,
          tags: Array.isArray(jikanChar.nicknames) ? jikanChar.nicknames : [],
          fandom: jikanChar.anime?.length > 0 ? 'Anime' : jikanChar.manga?.length > 0 ? 'Manga' : 'Other',
          gender: 'Unknown',
          popularityScore: Math.min(parseFloat((jikanChar.favorites || 0).toString()) / 100, 1000),
          sourceUrl: jikanChar.url || null,
        };

        console.log(`Syncing ${jikanChar.name} from ${series} (${jikanChar.favorites} favorites)`);

        // Controlla se esiste già per nome E serie (non solo nome)
        const existing = await prisma.character.findFirst({
          where: {
            AND: [
              { name: jikanChar.name },
              { series: series },
            ],
          },
        });

        if (existing) {
          await prisma.character.update({
            where: { id: existing.id },
            data: characterData,
          });
          updatedCount++;
          console.log(`Updated ${jikanChar.name}`);
        } else {
          await prisma.character.create({
            data: characterData,
          });
          syncedCount++;
          console.log(`Created ${jikanChar.name}`);
        }

      } catch (error) {
        console.error(`Error syncing character ${jikanChar.name}:`, error);
        errors.push(`Failed to sync ${jikanChar.name}: ${error}`);
      }
    }

    return {
      success: errors.length === 0,
      syncedCount,
      updatedCount,
      errors,
    };

  } catch (error) {
    console.error('Sync failed:', error);
    return {
      success: false,
      syncedCount: 0,
      updatedCount: 0,
      errors: [`Sync failed: ${error}`],
    };
  }
}

// Funzione per aggiornare i Google Trends per tutti i personaggi
async function updateGoogleTrends() {
  try {
    console.log('Starting Google Trends update...');
    
    // Prendi tutti i personaggi dal database
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

    // Processa i personaggi in batch per rispettare i rate limit
    const batchSize = 5;
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

        // Pausa tra i batch per rispettare i rate limit
        if (i + batchSize < characters.length) {
          await new Promise(resolve => setTimeout(resolve, 2000));
        }

      } catch (error) {
        console.error(`Error processing batch ${Math.floor(i / batchSize) + 1}:`, error);
        errors.push(`Failed to process batch ${Math.floor(i / batchSize) + 1}: ${error}`);
        errorCount += batch.length;
      }
    }

    return {
      success: errorCount < characters.length / 2, // Successo se meno del 50% ha errori
      updatedCount,
      errorCount,
      totalCharacters: characters.length,
      errors
    };

  } catch (error) {
    console.error('Google Trends update failed:', error);
    return {
      success: false,
      updatedCount: 0,
      errorCount: 0,
      totalCharacters: 0,
      errors: [`Google Trends update failed: ${error}`]
    };
  }
}

export async function POST(request: NextRequest) {
  try {
    const { action, source } = await request.json();
    const syncService = new CharacterSyncService();

    switch (action) {
      case 'sync':
        let result;
        
        if (source === 'anilist') {
          result = await syncService.syncAniListCharacters();
        } else if (source === 'jikan') {
          result = await syncService.syncDailyCharacters();
        } else {
          // Sync both sources by default
          const jikanResult = await syncService.syncDailyCharacters();
          const anilistResult = await syncService.syncAniListCharacters();
          
          result = {
            success: jikanResult.success && anilistResult.success,
            syncedCount: jikanResult.syncedCount + anilistResult.syncedCount,
            updatedCount: jikanResult.updatedCount + anilistResult.updatedCount,
            errors: [...jikanResult.errors, ...anilistResult.errors],
            sources: {
              jikan: jikanResult,
              anilist: anilistResult,
            },
          };
        }
        
        return NextResponse.json(result);

      case 'enhance':
        // Migliora i personaggi Jikan con dati AniList
        const enhanceResult = await syncService.enhanceJikanCharactersWithAniList();
        return NextResponse.json(enhanceResult);

      case 'full-sync':
        // Sincronizzazione completa: sync + merge + enhance
        console.log('Starting full sync process...');
        
        // 1. Sync entrambe le fonti
        const jikanFullResult = await syncService.syncDailyCharacters();
        const anilistFullResult = await syncService.syncAniListCharacters();
        
        // 2. Merge duplicati automaticamente
        const duplicatesByName = await prisma.character.groupBy({
          by: ['name'],
          having: {
            name: {
              _count: {
                gt: 1
              }
            }
          },
          _count: {
            name: true
          }
        });

        let mergedCount = 0;
        let deletedCount = 0;
        const mergeErrors: string[] = [];

        for (const duplicate of duplicatesByName) {
          try {
            const characters = await prisma.character.findMany({
              where: { name: duplicate.name },
              include: { trends: true }
            });

            if (characters.length < 2) continue;

            // Stesso algoritmo di merge dei duplicati
            const bestCharacter = characters.reduce((best, current) => {
              if (current.source === 'anilist' && current.series !== 'Unknown') {
                if (best.source !== 'anilist' || best.series === 'Unknown') {
                  return current;
                }
              }
              if (current.popularity > best.popularity) {
                return current;
              }
              return best;
            });

            // Merge dei dati
            const mergedData = {
              name: bestCharacter.name,
              series: bestCharacter.series !== 'Unknown' ? bestCharacter.series : 
                     characters.find(c => c.series !== 'Unknown')?.series || bestCharacter.series,
              category: bestCharacter.category,
              difficulty: Math.max(...characters.map(c => c.difficulty)),
              popularity: Math.max(...characters.map(c => c.popularity)),
              popularityScore: Math.max(...characters.map(c => c.popularityScore)),
              imageUrl: bestCharacter.imageUrl || characters.find(c => c.imageUrl)?.imageUrl,
              description: bestCharacter.description || characters.find(c => c.description)?.description,
              tags: Array.from(new Set(characters.flatMap(c => c.tags))),
              gender: bestCharacter.gender !== 'Unknown' ? bestCharacter.gender :
                     characters.find(c => c.gender !== 'Unknown')?.gender || bestCharacter.gender,
              source: bestCharacter.source,
              media_title: bestCharacter.media_title || characters.find(c => c.media_title)?.media_title,
              anilistId: bestCharacter.anilistId || characters.find(c => c.anilistId)?.anilistId,
              sourceUrl: bestCharacter.sourceUrl || characters.find(c => c.sourceUrl)?.sourceUrl
            };

            await prisma.character.update({
              where: { id: bestCharacter.id },
              data: mergedData
            });

            // Riassegna trend data
            const allTrends = characters.flatMap(c => c.trends);
            for (const trend of allTrends) {
              if (trend.characterId !== bestCharacter.id) {
                await prisma.trendData.update({
                  where: { id: trend.id },
                  data: { characterId: bestCharacter.id }
                });
              }
            }

            // Elimina duplicati
            const toDelete = characters.filter(c => c.id !== bestCharacter.id);
            for (const charToDelete of toDelete) {
              await prisma.character.delete({
                where: { id: charToDelete.id }
              });
              deletedCount++;
            }

            mergedCount++;
          } catch (error) {
            mergeErrors.push(`Failed to merge ${duplicate.name}: ${error}`);
          }
        }

        // 3. Enhance caratteri Jikan con dati AniList
        const enhanceFullResult = await syncService.enhanceJikanCharactersWithAniList();

        // 4. Update Google Trends data for all characters
        console.log('Starting Google Trends update...');
        const trendUpdateResult = await updateGoogleTrends();

        const fullResult = {
          success: jikanFullResult.success && anilistFullResult.success && enhanceFullResult.success && trendUpdateResult.success,
          sync: {
            jikan: jikanFullResult,
            anilist: anilistFullResult,
            totalSyncedCount: jikanFullResult.syncedCount + anilistFullResult.syncedCount,
            totalUpdatedCount: jikanFullResult.updatedCount + anilistFullResult.updatedCount
          },
          merge: {
            mergedCount,
            deletedCount,
            errors: mergeErrors
          },
          enhance: enhanceFullResult,
          trends: trendUpdateResult,
          errors: [
            ...jikanFullResult.errors,
            ...anilistFullResult.errors,
            ...mergeErrors,
            ...enhanceFullResult.errors,
            ...trendUpdateResult.errors
          ]
        };
        
        return NextResponse.json(fullResult);

      case 'update-trends':
        // Aggiorna solo i Google Trends per tutti i personaggi
        const trendOnlyResult = await updateGoogleTrends();
        return NextResponse.json(trendOnlyResult);

      case 'status':
        const totalCharacters = await prisma.character.count();
        const recentTrends = await prisma.trendData.count({
          where: {
            date: {
              gte: new Date(Date.now() - 24 * 60 * 60 * 1000), // Ultime 24 ore
            },
          },
        });
        
        // TODO: Riabilitare quando i modelli Prisma sono disponibili
        // const recentGoogleTrends = await prisma.googleTrendData.count({
        //   where: {
        //     date: {
        //       gte: new Date(Date.now() - 24 * 60 * 60 * 1000), // Ultime 24 ore
        //     },
        //   },
        // });

        // const trendSummaries = await prisma.trendSummary.count();

        return NextResponse.json({
          status: { isRunning: false },
          stats: {
            totalCharacters,
            recentTrends,
            // recentGoogleTrends,
            // trendSummaries,
            lastSyncDate: new Date().toISOString(),
          },
          message: 'Character sync service status',
        });

      case 'clean':
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

        const result2 = await prisma.trendData.deleteMany({
          where: {
            date: {
              lt: thirtyDaysAgo,
            },
          },
        });

        return NextResponse.json({ cleanedCount: result2.count });

      default:
        return NextResponse.json(
          { error: 'Invalid action. Use: sync, sync-jikan, status, or clean' },
          { status: 400 }
        );
    }
  } catch (error) {
    console.error('Sync API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const totalCharacters = await prisma.character.count();
    const recentTrends = await prisma.trendData.count({
      where: {
        date: {
          gte: new Date(Date.now() - 24 * 60 * 60 * 1000),
        },
      },
    });

    return NextResponse.json({
      status: { isRunning: false },
      stats: {
        totalCharacters,
        recentTrends,
        lastSyncDate: new Date().toISOString(),
      },
      message: 'Character sync service status',
    });
  } catch (error) {
    console.error('Sync status error:', error);
    return NextResponse.json(
      { error: 'Failed to get sync status' },
      { status: 500 }
    );
  }
}

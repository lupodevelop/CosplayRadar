import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@cosplayradar/db';

export async function GET(request: NextRequest) {
  try {
    console.log('Checking for duplicate characters...');
    
    // Query per trovare duplicati per nome
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

    // Query per trovare duplicati per nome + serie
    const duplicatesByNameAndSeries = await prisma.character.groupBy({
      by: ['name', 'series'],
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

    // Ottieni i dettagli dei duplicati
    const duplicateDetails = [];
    
    for (const duplicate of duplicatesByName) {
      const characters = await prisma.character.findMany({
        where: {
          name: duplicate.name
        },
        select: {
          id: true,
          name: true,
          series: true,
          source: true,
          anilistId: true,
          popularity: true,
          createdAt: true,
          updatedAt: true
        }
      });
      
      duplicateDetails.push({
        name: duplicate.name,
        count: duplicate._count.name,
        characters: characters
      });
    }

    // Statistiche generali
    const totalCharacters = await prisma.character.count();
    const totalUniqueNames = await prisma.character.groupBy({
      by: ['name'],
      _count: { name: true }
    });

    return NextResponse.json({
      success: true,
      stats: {
        totalCharacters,
        uniqueNames: totalUniqueNames.length,
        duplicateNames: duplicatesByName.length,
        duplicateNameAndSeries: duplicatesByNameAndSeries.length
      },
      duplicates: {
        byName: duplicateDetails,
        byNameAndSeries: duplicatesByNameAndSeries
      }
    });
    
  } catch (error) {
    console.error('Error checking duplicates:', error);
    
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const { action } = await request.json();
    
    if (action === 'merge') {
      console.log('Starting duplicate merge process...');
      
      // Trova tutti i duplicati per nome
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
      const errors: string[] = [];

      // Processa ogni gruppo di duplicati
      for (const duplicate of duplicatesByName) {
        try {
          const characters = await prisma.character.findMany({
            where: {
              name: duplicate.name
            },
            include: {
              trends: true
            }
          });

          if (characters.length < 2) continue;

          // Determina il personaggio "migliore" da mantenere
          // Priorità: 1) AniList con serie nota, 2) Jikan con più popolarità
          const bestCharacter = characters.reduce((best, current) => {
            // Preferisci AniList se ha serie non "Unknown"
            if (current.source === 'anilist' && current.series !== 'Unknown') {
              if (best.source !== 'anilist' || best.series === 'Unknown') {
                return current;
              }
            }
            
            // Se entrambi sono AniList o Jikan, preferisci quello con più popolarità
            if (current.popularity > best.popularity) {
              return current;
            }
            
            return best;
          });

          // Unisci i dati dal personaggio migliore
          const mergedData = {
            // Mantieni i dati migliori
            name: bestCharacter.name,
            series: bestCharacter.series !== 'Unknown' ? bestCharacter.series : 
                   characters.find(c => c.series !== 'Unknown')?.series || bestCharacter.series,
            category: bestCharacter.category,
            difficulty: Math.max(...characters.map(c => c.difficulty)),
            popularity: Math.max(...characters.map(c => c.popularity)),
            popularityScore: Math.max(...characters.map(c => c.popularityScore)),
            imageUrl: bestCharacter.imageUrl || characters.find(c => c.imageUrl)?.imageUrl,
            description: bestCharacter.description || characters.find(c => c.description)?.description,
            tags: Array.from(new Set(characters.flatMap(c => c.tags))), // Unisci tutti i tag
            gender: bestCharacter.gender !== 'Unknown' ? bestCharacter.gender :
                   characters.find(c => c.gender !== 'Unknown')?.gender || bestCharacter.gender,
            source: bestCharacter.source, // Mantieni la fonte migliore
            media_title: bestCharacter.media_title || characters.find(c => c.media_title)?.media_title,
            anilistId: bestCharacter.anilistId || characters.find(c => c.anilistId)?.anilistId,
            sourceUrl: bestCharacter.sourceUrl || characters.find(c => c.sourceUrl)?.sourceUrl
          };

          // Aggiorna il personaggio migliore con i dati uniti
          await prisma.character.update({
            where: { id: bestCharacter.id },
            data: mergedData
          });

          // Raccogli tutti i trend data dagli altri personaggi
          const allTrends = characters.flatMap(c => c.trends);
          
          // Riassegna i trend data al personaggio migliore
          for (const trend of allTrends) {
            if (trend.characterId !== bestCharacter.id) {
              await prisma.trendData.update({
                where: { id: trend.id },
                data: { characterId: bestCharacter.id }
              });
            }
          }

          // Elimina i duplicati (tutti tranne il migliore)
          const toDelete = characters.filter(c => c.id !== bestCharacter.id);
          for (const charToDelete of toDelete) {
            await prisma.character.delete({
              where: { id: charToDelete.id }
            });
            deletedCount++;
          }

          mergedCount++;
          console.log(`Merged ${duplicate.name}: kept ${bestCharacter.source} version (${bestCharacter.id}), deleted ${toDelete.length} duplicates`);
          
        } catch (error) {
          console.error(`Error merging ${duplicate.name}:`, error);
          errors.push(`Failed to merge ${duplicate.name}: ${error}`);
        }
      }

      return NextResponse.json({
        success: errors.length === 0,
        mergedCount,
        deletedCount,
        errors
      });
    }

    return NextResponse.json({
      success: false,
      error: 'Invalid action. Use: merge'
    }, { status: 400 });
    
  } catch (error) {
    console.error('Error in duplicate merge:', error);
    
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

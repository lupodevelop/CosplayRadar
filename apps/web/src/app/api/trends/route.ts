import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@cosplayradar/db';
import { simpleGoogleTrendsDbService } from '@/services/simpleGoogleTrendsDbService';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    
    // Parametri di filtering
    const region = searchParams.get('region') || 'GLOBAL';
    const keywordType = searchParams.get('keywordType') || 'COSPLAY';
    const timeframe = searchParams.get('timeframe') || '7d'; // 7d, 30d, 90d
    const minTrendScore = parseFloat(searchParams.get('minTrendScore') || '0');
    const maxTrendScore = parseFloat(searchParams.get('maxTrendScore') || '100');
    const sortBy = searchParams.get('sortBy') || 'trend7d'; // trend7d, trend30d, trend90d, confidence
    const sortOrder = searchParams.get('sortOrder') || 'desc';
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');
    const characterName = searchParams.get('characterName');
    const series = searchParams.get('series');

    // Offset per paginazione
    const offset = (page - 1) * limit;

    // Costruisci la query dinamicamente
    const whereClause: any = {
      AND: []
    };

    // Filtri sui trend
    if (region !== 'ALL') {
      whereClause.AND.push({ region: region });
    }

    if (keywordType !== 'ALL') {
      whereClause.AND.push({ keywordType: keywordType });
    }

    // Filtro per score basato sul timeframe
    const trendField = timeframe === '30d' ? 'trend30d' : timeframe === '90d' ? 'trend90d' : 'trend7d';
    whereClause.AND.push({
      [trendField]: {
        gte: minTrendScore,
        lte: maxTrendScore
      }
    });

    // Filtri sui personaggi
    if (characterName) {
      whereClause.AND.push({
        character: {
          name: {
            contains: characterName,
            mode: 'insensitive'
          }
        }
      });
    }

    if (series) {
      whereClause.AND.push({
        character: {
          series: {
            contains: series,
            mode: 'insensitive'
          }
        }
      });
    }

    // Prova a ottenere i trend usando il servizio semplificato
    try {
      const topTrends = await simpleGoogleTrendsDbService.getTopTrends(limit);
      
      // Filtra i risultati in base ai parametri
      const filteredTrends = topTrends.filter(trend => {
        if (characterName && !trend.character.name.toLowerCase().includes(characterName.toLowerCase())) {
          return false;
        }
        if (series && !trend.character.series.toLowerCase().includes(series.toLowerCase())) {
          return false;
        }
        if (keywordType !== 'ALL' && trend.keywordType !== keywordType) {
          return false;
        }
        return true;
      });

      const totalCount = filteredTrends.length;
      const paginatedTrends = filteredTrends.slice(offset, offset + limit);

      // Calcola statistiche
      const stats = {
        totalTrends: totalCount,
        currentPage: page,
        totalPages: Math.ceil(totalCount / limit),
        hasNextPage: page < Math.ceil(totalCount / limit),
        hasPrevPage: page > 1
      };

      return NextResponse.json({
        success: true,
        data: paginatedTrends,
        stats,
        filters: {
          region,
          keywordType,
          timeframe,
          minTrendScore,
          maxTrendScore,
          sortBy,
          sortOrder,
          characterName,
          series
        }
      });

    } catch (error) {
      console.warn('Simple trends service not available, falling back to character data:', error);
      
      // Fallback: restituisci solo i personaggi senza trend data
      const characters = await prisma.character.findMany({
        where: {
          ...(characterName && {
            name: {
              contains: characterName,
              mode: 'insensitive'
            }
          }),
          ...(series && {
            series: {
              contains: series,
              mode: 'insensitive'
            }
          })
        },
        select: {
          id: true,
          name: true,
          series: true,
          category: true,
          imageUrl: true,
          popularityScore: true,
          gender: true
        },
        orderBy: {
          popularityScore: 'desc'
        },
        skip: offset,
        take: limit
      });

      const totalCount = await prisma.character.count({
        where: {
          ...(characterName && {
            name: {
              contains: characterName,
              mode: 'insensitive'
            }
          }),
          ...(series && {
            series: {
              contains: series,
              mode: 'insensitive'
            }
          })
        }
      });

      return NextResponse.json({
        success: true,
        data: characters.map(char => ({
          id: char.id,
          character: char,
          trend7d: 0,
          trend30d: 0,
          trend90d: 0,
          confidence: 0,
          region: 'GLOBAL',
          keywordType: 'COSPLAY',
          keyword: char.name,
          queryVolume: 'LOW',
          date: new Date().toISOString()
        })),
        stats: {
          totalTrends: totalCount,
          currentPage: page,
          totalPages: Math.ceil(totalCount / limit),
          hasNextPage: page < Math.ceil(totalCount / limit),
          hasPrevPage: page > 1
        },
        filters: {
          region,
          keywordType,
          timeframe,
          minTrendScore,
          maxTrendScore,
          sortBy,
          sortOrder,
          characterName,
          series
        },
        warning: 'Google Trends data not available, showing character data only'
      });
    }

  } catch (error) {
    console.error('Trends query API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

// Endpoint per ottenere le summaries aggregate
export async function POST(request: NextRequest) {
  try {
    const { action, characterIds } = await request.json();

    if (action === 'summaries') {
      // Restituisci le summaries aggregate per i personaggi richiesti
      const whereClause = characterIds && characterIds.length > 0 
        ? { characterId: { in: characterIds } }
        : {};

      try {
        // @ts-ignore
        const summaries = await prisma.trendSummary.findMany({
          where: whereClause,
          include: {
            character: {
              select: {
                id: true,
                name: true,
                series: true,
                category: true,
                imageUrl: true,
                popularityScore: true,
                gender: true
              }
            }
          },
          orderBy: {
            overallTrendScore: 'desc'
          },
          take: 50
        });

        return NextResponse.json({
          success: true,
          data: summaries
        });

      } catch (error) {
        console.warn('Trend summaries not available:', error);
        return NextResponse.json({
          success: false,
          error: 'Trend summaries not available yet',
          data: []
        });
      }
    }

    return NextResponse.json(
      { error: 'Invalid action' },
      { status: 400 }
    );

  } catch (error) {
    console.error('Trends summaries API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

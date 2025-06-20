import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@cosplayradar/db';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const analysisType = searchParams.get('type') || 'market-overview';
    const region = searchParams.get('region') || 'GLOBAL';
    const timeframe = searchParams.get('timeframe') || '7d';
    const limit = parseInt(searchParams.get('limit') || '20');

    switch (analysisType) {
      case 'market-overview':
        return await getMarketOverview(region, timeframe, limit);
      
      case 'rising-trends':
        return await getRisingTrends(region, timeframe, limit);
      
      case 'top-cosplay':
        return await getTopCosplayTrends(region, timeframe, limit);
      
      case 'regional-comparison':
        return await getRegionalComparison(timeframe, limit);
      
      case 'character-opportunities':
        return await getCharacterOpportunities(region, timeframe, limit);
      
      case 'market-gaps':
        return await getMarketGaps(region, limit);
      
      default:
        return NextResponse.json(
          { error: 'Invalid analysis type. Available: market-overview, rising-trends, top-cosplay, regional-comparison, character-opportunities, market-gaps' },
          { status: 400 }
        );
    }

  } catch (error) {
    console.error('Market analysis API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

// Panoramica del mercato
async function getMarketOverview(region: string, timeframe: string, limit: number) {
  try {
    const trendField = timeframe === '30d' ? 'trend30d' : timeframe === '90d' ? 'trend90d' : 'trend7d';

    const topCosplayTrends = await prisma.googleTrendData.findMany({
      where: {
        region: region as any,
        keywordType: 'COSPLAY',
        [trendField]: { gt: 0 }
      },
      include: {
        character: {
          select: {
            id: true,
            name: true,
            series: true,
            category: true,
            imageUrl: true,
            gender: true
          }
        }
      },
      orderBy: {
        [trendField]: 'desc'
      },
      take: limit
    });

    const topCharacterTrends = await prisma.googleTrendData.findMany({
      where: {
        region: region as any,
        keywordType: 'CHARACTER', 
        [trendField]: { gt: 0 }
      },
      include: {
        character: {
          select: {
            id: true,
            name: true,
            series: true,
            category: true,
            imageUrl: true,
            gender: true
          }
        }
      },
      orderBy: {
        [trendField]: 'desc'
      },
      take: limit
    });

    const risingTrends = await prisma.googleTrendData.findMany({
      where: {
        region: region as any,
        keywordType: 'COSPLAY',
        confidence: { gte: 0.7 },
        [trendField]: { gt: 0 }
      },
      include: {
        character: {
          select: {
            id: true,
            name: true,
            series: true,
            category: true,
            imageUrl: true,
            gender: true
          }
        }
      },
      orderBy: [
        { [trendField]: 'desc' },
        { confidence: 'desc' }
      ],
      take: Math.min(limit, 10)
    });

    // Calcola statistiche
    const totalTrends = topCosplayTrends.length + topCharacterTrends.length;
    const avgCosplayScore = topCosplayTrends.reduce((sum, t) => sum + (t as any)[trendField], 0) / topCosplayTrends.length || 0;
    const avgCharacterScore = topCharacterTrends.reduce((sum, t) => sum + (t as any)[trendField], 0) / topCharacterTrends.length || 0;

    return NextResponse.json({
      success: true,
      data: {
        region,
        timeframe,
        topCosplayTrends,
        topCharacterTrends,
        risingTrends,
        statistics: {
          totalTrends,
          avgCosplayScore: Math.round(avgCosplayScore * 100) / 100,
          avgCharacterScore: Math.round(avgCharacterScore * 100) / 100,
          risingTrendsCount: risingTrends.length
        }
      }
    });

  } catch (error) {
    console.warn('Market overview not available, using fallback:', error);
    return getFallbackMarketOverview(region, timeframe, limit);
  }
}

// Trend in crescita
async function getRisingTrends(region: string, timeframe: string, limit: number) {
  try {
    const trendField = timeframe === '30d' ? 'trend30d' : timeframe === '90d' ? 'trend90d' : 'trend7d';
    const prevTrendField = timeframe === '30d' ? 'trend7d' : timeframe === '90d' ? 'trend30d' : null;

    let whereClause: any = {
      region: region as any,
      keywordType: 'COSPLAY',
      [trendField]: { gt: 0 },
      confidence: { gte: 0.6 }
    };

    // Se possibile, confronta con il periodo precedente per identificare crescita
    if (prevTrendField) {
      const risingTrends = await prisma.$queryRaw`
        SELECT *, 
               (${trendField} - ${prevTrendField}) as growth_rate
        FROM google_trend_data
        WHERE region = ${region}
          AND keyword_type = 'COSPLAY'
          AND ${trendField} > 0
          AND confidence >= 0.6
          AND (${trendField} - ${prevTrendField}) > 0
        ORDER BY growth_rate DESC, ${trendField} DESC
        LIMIT ${limit}
      `;

      return NextResponse.json({
        success: true,
        data: {
          region,
          timeframe,
          risingTrends,
          analysisType: 'growth-based'
        }
      });
    }

    // Fallback: ordina per score senza confronto
    const risingTrends = await prisma.googleTrendData.findMany({
      where: whereClause,
      include: {
        character: {
          select: {
            id: true,
            name: true,
            series: true,
            category: true,
            imageUrl: true,
            gender: true
          }
        }
      },
      orderBy: [
        { [trendField]: 'desc' },
        { confidence: 'desc' }
      ],
      take: limit
    });

    return NextResponse.json({
      success: true,
      data: {
        region,
        timeframe,
        risingTrends,
        analysisType: 'score-based'
      }
    });

  } catch (error) {
    console.warn('Rising trends not available:', error);
    return NextResponse.json({
      success: false,
      error: 'Rising trends analysis not available yet',
      data: []
    });
  }
}

// Top trend cosplay
async function getTopCosplayTrends(region: string, timeframe: string, limit: number) {
  try {
    const trendField = timeframe === '30d' ? 'trend30d' : timeframe === '90d' ? 'trend90d' : 'trend7d';

    const topCosplayTrends = await prisma.googleTrendData.findMany({
      where: {
        region: region as any,
        keywordType: 'COSPLAY',
        [trendField]: { gt: 0 }
      },
      include: {
        character: {
          select: {
            id: true,
            name: true,
            series: true,
            category: true,
            imageUrl: true,
            gender: true,
            difficulty: true
          }
        }
      },
      orderBy: {
        [trendField]: 'desc'
      },
      take: limit
    });

    // Categorizza per difficoltà
    const byDifficulty = {
      easy: topCosplayTrends.filter(t => t.character.difficulty <= 2),
      medium: topCosplayTrends.filter(t => t.character.difficulty === 3),
      hard: topCosplayTrends.filter(t => t.character.difficulty >= 4)
    };

    // Categorizza per genere
    const byGender = {
      male: topCosplayTrends.filter(t => t.character.gender?.toLowerCase() === 'male'),
      female: topCosplayTrends.filter(t => t.character.gender?.toLowerCase() === 'female'),
      other: topCosplayTrends.filter(t => !t.character.gender || !['male', 'female'].includes(t.character.gender.toLowerCase()))
    };

    return NextResponse.json({
      success: true,
      data: {
        region,
        timeframe,
        allTrends: topCosplayTrends,
        byDifficulty,
        byGender,
        statistics: {
          totalTrends: topCosplayTrends.length,
          avgScore: topCosplayTrends.reduce((sum, t) => sum + (t as any)[trendField], 0) / topCosplayTrends.length || 0,
          difficultyDistribution: {
            easy: byDifficulty.easy.length,
            medium: byDifficulty.medium.length,
            hard: byDifficulty.hard.length
          },
          genderDistribution: {
            male: byGender.male.length,
            female: byGender.female.length,
            other: byGender.other.length
          }
        }
      }
    });

  } catch (error) {
    console.warn('Top cosplay trends not available:', error);
    return NextResponse.json({
      success: false,
      error: 'Top cosplay trends not available yet',
      data: []
    });
  }
}

// Confronto regionale
async function getRegionalComparison(timeframe: string, limit: number) {
  try {
    const trendField = timeframe === '30d' ? 'trend30d' : timeframe === '90d' ? 'trend90d' : 'trend7d';
    const regions = ['GLOBAL', 'US', 'JP', 'IT', 'UK', 'DE', 'FR'];

    const regionalData: any = {};

    for (const region of regions) {
      try {
        const regionTrends = await prisma.googleTrendData.findMany({
          where: {
            region: region as any,
            keywordType: 'COSPLAY',
            [trendField]: { gt: 0 }
          },
          include: {
            character: {
              select: {
                id: true,
                name: true,
                series: true,
                category: true
              }
            }
          },
          orderBy: {
            [trendField]: 'desc'
          },
          take: limit
        });

        regionalData[region] = {
          trends: regionTrends,
          avgScore: regionTrends.reduce((sum, t) => sum + (t as any)[trendField], 0) / regionTrends.length || 0,
          topCharacter: regionTrends[0]?.character?.name || 'N/A',
          totalTrends: regionTrends.length
        };
      } catch (error) {
        regionalData[region] = {
          trends: [],
          avgScore: 0,
          topCharacter: 'N/A',
          totalTrends: 0,
          error: 'Data not available'
        };
      }
    }

    return NextResponse.json({
      success: true,
      data: {
        timeframe,
        regionalData,
        comparison: {
          bestPerformingRegion: Object.entries(regionalData)
            .sort(([,a]: any, [,b]: any) => b.avgScore - a.avgScore)[0]?.[0] || 'N/A',
          totalRegionsAnalyzed: regions.length
        }
      }
    });

  } catch (error) {
    console.warn('Regional comparison not available:', error);
    return NextResponse.json({
      success: false,
      error: 'Regional comparison not available yet',
      data: []
    });
  }
}

// Opportunità per personaggi
async function getCharacterOpportunities(region: string, timeframe: string, limit: number) {
  try {
    // Personaggi con alto interesse generale ma basso interesse cosplay (opportunità)
    const trendField = timeframe === '30d' ? 'trend30d' : timeframe === '90d' ? 'trend90d' : 'trend7d';

    // Query complessa per trovare personaggi con gap tra interesse generale e cosplay
    const opportunities = await prisma.$queryRaw`
      SELECT 
        c.id, c.name, c.series, c.category, c.image_url, c.gender, c.difficulty,
        char_trends.${trendField} as character_trend,
        COALESCE(cos_trends.${trendField}, 0) as cosplay_trend,
        (char_trends.${trendField} - COALESCE(cos_trends.${trendField}, 0)) as opportunity_gap
      FROM characters c
      JOIN google_trend_data char_trends ON c.id = char_trends.character_id
      LEFT JOIN google_trend_data cos_trends ON c.id = cos_trends.character_id 
        AND cos_trends.keyword_type = 'COSPLAY' 
        AND cos_trends.region = ${region}
      WHERE char_trends.keyword_type = 'CHARACTER'
        AND char_trends.region = ${region}
        AND char_trends.${trendField} > 20
        AND (cos_trends.${trendField} IS NULL OR cos_trends.${trendField} < char_trends.${trendField} * 0.3)
      ORDER BY opportunity_gap DESC
      LIMIT ${limit}
    `;

    return NextResponse.json({
      success: true,
      data: {
        region,
        timeframe,
        opportunities,
        analysisNote: 'Characters with high general interest but low cosplay interest represent opportunities'
      }
    });

  } catch (error) {
    console.warn('Character opportunities analysis not available:', error);
    return NextResponse.json({
      success: false,
      error: 'Character opportunities analysis not available yet',
      data: []
    });
  }
}

// Gap di mercato
async function getMarketGaps(region: string, limit: number) {
  try {
    // Analizza gap per genere, difficoltà, categoria
    const characters = await prisma.character.findMany({
      select: {
        id: true,
        name: true,
        series: true,
        category: true,
        gender: true,
        difficulty: true,
        imageUrl: true
      },
      take: limit * 3 // Prendiamo più dati per l'analisi
    });

    // Analizza la distribuzione
    const genderDistribution = characters.reduce((acc, char) => {
      const gender = char.gender?.toLowerCase() || 'unknown';
      acc[gender] = (acc[gender] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const difficultyDistribution = characters.reduce((acc, char) => {
      const difficulty = char.difficulty.toString();
      acc[difficulty] = (acc[difficulty] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const categoryDistribution = characters.reduce((acc, char) => {
      const category = char.category;
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Identifica i gap (categorie sotto-rappresentate)
    const gaps = {
      underrepresentedGenders: Object.entries(genderDistribution)
        .filter(([_, count]) => count < characters.length * 0.15)
        .map(([gender, count]) => ({ gender, count, percentage: (count / characters.length) * 100 })),
      
      underrepresentedDifficulties: Object.entries(difficultyDistribution)
        .filter(([_, count]) => count < characters.length * 0.15)
        .map(([difficulty, count]) => ({ difficulty, count, percentage: (count / characters.length) * 100 })),
      
      underrepresentedCategories: Object.entries(categoryDistribution)
        .filter(([_, count]) => count < characters.length * 0.20)
        .map(([category, count]) => ({ category, count, percentage: (count / characters.length) * 100 }))
    };

    return NextResponse.json({
      success: true,
      data: {
        region,
        totalCharacters: characters.length,
        distributions: {
          gender: genderDistribution,
          difficulty: difficultyDistribution,
          category: categoryDistribution
        },
        marketGaps: gaps,
        recommendations: [
          'Consider focusing on underrepresented character types',
          'Balance portfolio across different difficulties and genders',
          'Explore niche categories with growth potential'
        ]
      }
    });

  } catch (error) {
    console.error('Market gaps analysis failed:', error);
    return NextResponse.json({
      success: false,
      error: 'Market gaps analysis failed',
      data: []
    });
  }
}

// Fallback per panoramica mercato
async function getFallbackMarketOverview(region: string, timeframe: string, limit: number) {
  const characters = await prisma.character.findMany({
    select: {
      id: true,
      name: true,
      series: true,
      category: true,
      imageUrl: true,
      gender: true,
      popularityScore: true,
      difficulty: true
    },
    orderBy: {
      popularityScore: 'desc'
    },
    take: limit
  });

  return NextResponse.json({
    success: true,
    data: {
      region,
      timeframe,
      topCosplayTrends: characters.slice(0, Math.ceil(limit / 2)),
      topCharacterTrends: characters.slice(Math.ceil(limit / 2)),
      risingTrends: characters.slice(0, 5),
      statistics: {
        totalTrends: characters.length,
        avgCosplayScore: 0,
        avgCharacterScore: 0,
        risingTrendsCount: 5
      }
    },
    warning: 'Using fallback data - Google Trends not available'
  });
}

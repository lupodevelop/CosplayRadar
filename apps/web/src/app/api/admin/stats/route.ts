import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@cosplayradar/db';

export async function GET(request: NextRequest) {
  try {
    console.log('Getting character statistics...');
    
    // Statistiche per genere
    const genderStats = await prisma.character.groupBy({
      by: ['gender'],
      _count: {
        gender: true
      },
      orderBy: {
        _count: {
          gender: 'desc'
        }
      }
    });

    // Statistiche per fonte
    const sourceStats = await prisma.character.groupBy({
      by: ['source'],
      _count: {
        source: true
      },
      orderBy: {
        _count: {
          source: 'desc'
        }
      }
    });

    // Statistiche per serie (top 10)
    const seriesStats = await prisma.character.groupBy({
      by: ['series'],
      _count: {
        series: true
      },
      where: {
        series: {
          not: 'Unknown'
        }
      },
      orderBy: {
        _count: {
          series: 'desc'
        }
      },
      take: 10
    });

    // Personaggi con genere sconosciuto che potrebbero essere migliorati
    const unknownGenderCount = await prisma.character.count({
      where: {
        OR: [
          { gender: 'Unknown' },
          { gender: null }
        ]
      }
    });

    // Personaggi con serie sconosciuta che potrebbero essere migliorati
    const unknownSeriesCount = await prisma.character.count({
      where: {
        series: 'Unknown'
      }
    });

    // Statistiche di popolarità
    const avgPopularity = await prisma.character.aggregate({
      _avg: {
        popularity: true
      }
    });

    const maxPopularity = await prisma.character.aggregate({
      _max: {
        popularity: true
      }
    });

    // Top 5 personaggi più popolari
    const topCharacters = await prisma.character.findMany({
      orderBy: {
        popularity: 'desc'
      },
      take: 5,
      select: {
        name: true,
        series: true,
        gender: true,
        source: true,
        popularity: true
      }
    });

    const totalCharacters = await prisma.character.count();

    return NextResponse.json({
      success: true,
      stats: {
        total: totalCharacters,
        byGender: genderStats,
        bySource: sourceStats,
        topSeries: seriesStats,
        dataQuality: {
          unknownGender: unknownGenderCount,
          unknownSeries: unknownSeriesCount,
          percentageWithKnownGender: ((totalCharacters - unknownGenderCount) / totalCharacters * 100).toFixed(1),
          percentageWithKnownSeries: ((totalCharacters - unknownSeriesCount) / totalCharacters * 100).toFixed(1)
        },
        popularity: {
          average: Math.round(avgPopularity._avg.popularity || 0),
          maximum: maxPopularity._max.popularity || 0
        },
        topCharacters
      }
    });
    
  } catch (error) {
    console.error('Error getting statistics:', error);
    
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

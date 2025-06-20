// Service per calcolare i percentili dinamici del trending
import { prisma } from '@cosplayradar/db';

interface TrendingTiers {
  trending: number;     // Top 10%
  hot: number;         // Top 25%
  rising: number;      // Top 50%
  stable: number;      // Top 75%
}

interface TrendingStats {
  totalCharacters: number;
  maxTrendingScore: number;
  minTrendingScore: number;
  avgTrendingScore: number;
}

interface TrendingApiResponse {
  tiers: TrendingTiers;
  stats: TrendingStats;
}

// Cache per evitare ricalcoli frequenti
let cachedTrendingTiers: TrendingApiResponse | null = null;
let cacheExpiration: number = 0;
const CACHE_DURATION = 15 * 60 * 1000; // 15 minuti

export async function getTrendingTiers(): Promise<TrendingApiResponse> {
  const now = Date.now();
  
  // Usa cache se valida
  if (cachedTrendingTiers && now < cacheExpiration) {
    console.log('📦 Using cached trending tiers');
    return cachedTrendingTiers;
  }

  try {
    console.log('🔄 Calculating trending tiers from database...');
    
    // Ottieni tutti i trending score dai personaggi che hanno un TrendSummary
    const charactersWithTrends = await prisma.character.findMany({
      include: {
        trendSummary: {
          select: {
            overallTrendScore: true
          }
        }
      },
      where: {
        trendSummary: {
          overallTrendScore: {
            gt: 0  // Solo personaggi con trending score > 0
          }
        }
      }
    });

    if (charactersWithTrends.length === 0) {
      console.log('⚠️ No characters with trending scores found');
      const emptyResult = {
        tiers: {
          trending: 0,
          hot: 0,
          rising: 0,
          stable: 0
        },
        stats: {
          totalCharacters: 0,
          maxTrendingScore: 0,
          minTrendingScore: 0,
          avgTrendingScore: 0
        }
      };
      
      // Cache anche il risultato vuoto per evitare query ripetute
      cachedTrendingTiers = emptyResult;
      cacheExpiration = now + CACHE_DURATION;
      
      return emptyResult;
    }

    const scores = charactersWithTrends
      .map(c => c.trendSummary?.overallTrendScore || 0)
      .filter(score => score > 0)
      .sort((a, b) => b - a);
    
    const totalCount = scores.length;
    
    // Calcola i percentili per il trending
    const getPercentileValue = (percentile: number) => {
      const index = Math.ceil((percentile / 100) * totalCount) - 1;
      return scores[Math.max(0, index)];
    };

    // Thresholds basati sui percentili:
    // - TRENDING: solo top 10% dei trending score
    // - HOT: top 25% 
    // - RISING: top 50%
    // - STABLE: sopra la mediana dei trending score
    const trendingThreshold = getPercentileValue(10);  // Top 10%
    const hotThreshold = getPercentileValue(25);       // Top 25%
    const risingThreshold = getPercentileValue(50);    // Top 50%
    const stableThreshold = getPercentileValue(75);    // Top 75%

    const stats = {
      totalCharacters: totalCount,
      maxTrendingScore: Math.max(...scores),
      minTrendingScore: Math.min(...scores),
      avgTrendingScore: scores.reduce((sum, score) => sum + score, 0) / totalCount
    };

    const tiers = {
      trending: trendingThreshold,
      hot: hotThreshold,
      rising: risingThreshold,
      stable: stableThreshold
    };

    const result = { tiers, stats };
    
    // Cache il risultato
    cachedTrendingTiers = result;
    cacheExpiration = now + CACHE_DURATION;

    console.log('📊 Trending tiers calculated and cached:', {
      tiers,
      stats,
      distribution: {
        trending: `${scores.filter(s => s >= trendingThreshold).length} characters (${((scores.filter(s => s >= trendingThreshold).length / totalCount) * 100).toFixed(1)}%)`,
        hot: `${scores.filter(s => s >= hotThreshold && s < trendingThreshold).length} characters`,
        rising: `${scores.filter(s => s >= risingThreshold && s < hotThreshold).length} characters`,
        stable: `${scores.filter(s => s >= stableThreshold && s < risingThreshold).length} characters`
      }
    });

    return result;

  } catch (error) {
    console.error('❌ Error calculating trending tiers:', error);
    throw error;
  }
}

export function clearTrendingCache(): void {
  cachedTrendingTiers = null;
  cacheExpiration = 0;
  console.log('🗑️ Trending cache cleared');
}

// Funzione per determinare il livello di trending basato sul score
export function getTrendingLevel(overallTrendScore: number, tiers: TrendingTiers): {
  level: 'TRENDING' | 'HOT' | 'RISING' | 'STABLE' | 'NONE';
  icon: string;
  color: string;
  bgColor: string;
} {
  if (overallTrendScore >= tiers.trending) {
    return {
      level: 'TRENDING',
      icon: '🔥',
      color: 'text-red-500',
      bgColor: 'bg-red-500'
    };
  } else if (overallTrendScore >= tiers.hot) {
    return {
      level: 'HOT',
      icon: '⚡',
      color: 'text-orange-500',
      bgColor: 'bg-orange-500'
    };
  } else if (overallTrendScore >= tiers.rising) {
    return {
      level: 'RISING',
      icon: '📈',
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500'
    };
  } else if (overallTrendScore >= tiers.stable) {
    return {
      level: 'STABLE',
      icon: '📊',
      color: 'text-blue-500',
      bgColor: 'bg-blue-500'
    };
  } else {
    return {
      level: 'NONE',
      icon: '',
      color: '',
      bgColor: ''
    };
  }
}

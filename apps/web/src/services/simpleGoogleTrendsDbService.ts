/**
 * Simple Google Trends Database Service
 * Usa solo i modelli esistenti fino a quando i nuovi modelli non saranno disponibili
 */

import { prisma } from '@cosplayradar/db';
import { SimpleBatchResult, SimpleTrendResult } from './simpleGoogleTrendsService';

interface SimpleTrendStorage {
  characterId: string;
  platform: string; // Useremo 'GOOGLE_TRENDS'
  mentions: number; // Trend score
  engagement: number; // Confidence
  sentiment: number; // Tipo di keyword (0=CHARACTER, 1=COSPLAY)
  date: Date;
}

class SimpleGoogleTrendsDbService {

  /**
   * Salva i trend data nel modello TrendData esistente
   */
  async saveTrendData(characterId: string, trends: SimpleTrendResult[]): Promise<void> {
    console.log(`Saving ${trends.length} trend data points for character ${characterId}`);

    try {
      // Elimina i vecchi dati Google Trends per questo personaggio
      await prisma.trendData.deleteMany({
        where: {
          characterId,
          platform: 'OTHER' // Usiamo OTHER per Google Trends
        }
      });

      // Salva i nuovi trend data
      for (const trend of trends) {
        await prisma.trendData.create({
          data: {
            characterId: trend.characterId,
            platform: 'OTHER', // Usiamo OTHER per Google Trends
            mentions: Math.round(trend.trend7d), // Score 7d come mentions
            engagement: trend.confidence, // Confidence come engagement
            sentiment: trend.keywordType === 'COSPLAY' ? 1 : 0, // Tipo keyword come sentiment
            date: new Date(trend.date)
          }
        });
      }

      console.log(`Saved ${trends.length} trend data points for character ${characterId}`);

    } catch (error) {
      console.error(`Error saving trend data for character ${characterId}:`, error);
      throw error;
    }
  }

  /**
   * Recupera i trend data per un personaggio
   */
  async getTrendData(characterId: string): Promise<SimpleTrendResult[]> {
    try {
      const trendData = await prisma.trendData.findMany({
        where: {
          characterId,
          platform: 'OTHER' // Google Trends data
        },
        orderBy: {
          date: 'desc'
        },
        take: 10 // Ultimi 10 record
      });

      return trendData.map(data => ({
        characterId: data.characterId,
        keyword: data.sentiment === 1 ? 'cosplay' : 'character',
        keywordType: data.sentiment === 1 ? 'COSPLAY' : 'CHARACTER',
        region: 'GLOBAL',
        trend7d: data.mentions,
        trend30d: data.mentions, // Usiamo lo stesso valore per ora
        confidence: data.engagement,
        date: data.date.toISOString()
      }));

    } catch (error) {
      console.error(`Error retrieving trend data for character ${characterId}:`, error);
      return [];
    }
  }

  /**
   * Ottieni statistiche sui trend
   */
  async getTrendStats(): Promise<{
    totalTrendData: number;
    recentTrendData: number;
    charactersWithTrends: number;
    avgTrendScore: number;
  }> {
    try {
      const totalTrendData = await prisma.trendData.count({
        where: {
          platform: 'OTHER' // Google Trends
        }
      });

      const recentTrendData = await prisma.trendData.count({
        where: {
          platform: 'OTHER',
          date: {
            gte: new Date(Date.now() - 24 * 60 * 60 * 1000) // Ultime 24 ore
          }
        }
      });

      const charactersWithTrends = await prisma.trendData.groupBy({
        by: ['characterId'],
        where: {
          platform: 'OTHER'
        },
        _count: {
          characterId: true
        }
      });

      const avgResult = await prisma.trendData.aggregate({
        where: {
          platform: 'OTHER'
        },
        _avg: {
          mentions: true
        }
      });

      return {
        totalTrendData,
        recentTrendData,
        charactersWithTrends: charactersWithTrends.length,
        avgTrendScore: avgResult._avg?.mentions || 0
      };

    } catch (error) {
      console.error('Error getting trend stats:', error);
      return {
        totalTrendData: 0,
        recentTrendData: 0,
        charactersWithTrends: 0,
        avgTrendScore: 0
      };
    }
  }

  /**
   * Pulisci i dati vecchi
   */
  async cleanOldTrendData(daysOld: number = 30): Promise<number> {
    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - daysOld);

      const result = await prisma.trendData.deleteMany({
        where: {
          platform: 'OTHER', // Google Trends
          date: {
            lt: cutoffDate
          }
        }
      });

      console.log(`Cleaned ${result.count} old trend data records`);
      return result.count;

    } catch (error) {
      console.error('Error cleaning old trend data:', error);
      return 0;
    }
  }

  /**
   * Ottieni top trends per regione/tipo
   */
  async getTopTrends(limit: number = 20): Promise<any[]> {
    try {
      const topTrends = await prisma.trendData.findMany({
        where: {
          platform: 'OTHER', // Google Trends
          mentions: {
            gt: 0
          }
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
          mentions: 'desc'
        },
        take: limit
      });

      return topTrends.map(trend => ({
        character: trend.character,
        trendScore: trend.mentions,
        confidence: trend.engagement,
        keywordType: trend.sentiment === 1 ? 'COSPLAY' : 'CHARACTER',
        date: trend.date,
        region: 'GLOBAL'
      }));

    } catch (error) {
      console.error('Error getting top trends:', error);
      return [];
    }
  }

  /**
   * Batch processing per salvare più personaggi
   */
  async batchSaveTrendData(batchResults: SimpleBatchResult[]): Promise<{
    success: boolean;
    saved: number;
    errors: string[];
  }> {
    let saved = 0;
    const errors: string[] = [];

    for (const result of batchResults) {
      try {
        if (result.trends.length > 0) {
          await this.saveTrendData(result.characterId, result.trends);
          saved++;
        }
        
        // Aggiungi errori dal batch
        errors.push(...result.errors);

      } catch (error) {
        console.error(`Error in batch save for character ${result.characterId}:`, error);
        errors.push(`Failed to save character ${result.characterId}: ${error}`);
      }
    }

    return {
      success: errors.length < batchResults.length,
      saved,
      errors
    };
  }
}

// Export singleton
export const simpleGoogleTrendsDbService = new SimpleGoogleTrendsDbService();
export default simpleGoogleTrendsDbService;

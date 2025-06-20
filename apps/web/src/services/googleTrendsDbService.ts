/**
 * Google Trends Database Service
 * Gestisce la persistenza dei trend multi-dimensionali nel database
 */

import { prisma } from '@cosplayradar/db';
import { googleTrendsService, TrendResult, BatchTrendResult } from './googleTrendsService';

// Tipi enum per Google Trends (definiti manualmente per compatibilità)
type TrendRegion = 'GLOBAL' | 'US' | 'JP' | 'IT' | 'UK' | 'DE' | 'FR' | 'BR' | 'KR' | 'CA' | 'AU' | 'MX';
type KeywordType = 'COSPLAY' | 'CHARACTER' | 'COSTUME' | 'FANART' | 'FIGURE' | 'MERCH' | 'GENERAL';
type QueryVolume = 'LOW' | 'MEDIUM' | 'HIGH' | 'VERY_HIGH';

interface TrendSummaryData {
  characterId: string;
  globalCosplayScore: number;
  globalCharacterScore: number;
  globalShoppingScore: number;
  usCosplayScore: number;
  jpCharacterScore: number;
  itCosplayScore: number;
  overallTrendScore: number;
  cosplayTrendScore: number;
  risingMarkets: string[];
  bestMarket: TrendRegion | null;
  dataQuality: number;
}

class GoogleTrendsDbService {

  /**
   * Salva trend data nel database per un personaggio
   */
  async saveTrendData(characterId: string, trends: TrendResult[]): Promise<void> {
    console.log(`Saving ${trends.length} trend data points for character ${characterId}`);

    // Elimina trend data vecchi per questo personaggio (mantieni solo gli ultimi)
    await prisma.googleTrendData.deleteMany({
      where: {
        characterId,
        date: {
          lt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) // Cancella dati più vecchi di 7 giorni
        }
      }
    });

    // Inserisci nuovi trend data
    for (const trend of trends) {
      try {
        await prisma.googleTrendData.upsert({
          where: {
            characterId_region_keywordType_keyword: {
              characterId,
              region: trend.region as TrendRegion,
              keywordType: trend.keywordType as KeywordType,
              keyword: trend.keyword
            }
          },
          update: {
            trend7d: trend.trend7d,
            trend30d: trend.trend30d,
            trend90d: trend.trend90d,
            confidence: trend.confidence,
            queryVolume: trend.queryVolume as QueryVolume,
            updatedAt: new Date()
          },
          create: {
            characterId,
            region: trend.region as TrendRegion,
            keywordType: trend.keywordType as KeywordType,
            keyword: trend.keyword,
            trend7d: trend.trend7d,
            trend30d: trend.trend30d,
            trend90d: trend.trend90d,
            confidence: trend.confidence,
            queryVolume: trend.queryVolume as QueryVolume
          }
        });
      } catch (error) {
        console.error(`Error saving trend data for ${trend.keyword}:`, error);
      }
    }

    console.log(`Successfully saved trend data for character ${characterId}`);
  }

  /**
   * Calcola e aggiorna il trend summary per un personaggio
   */
  async updateTrendSummary(characterId: string): Promise<void> {
    console.log(`Calculating trend summary for character ${characterId}`);

    // Ottieni tutti i trend data per questo personaggio
    const trendData = await prisma.googleTrendData.findMany({
      where: { characterId },
      orderBy: { date: 'desc' }
    });

    if (trendData.length === 0) {
      console.log(`No trend data found for character ${characterId}`);
      return;
    }

    // Calcola scores aggregati
    const summary = this.calculateTrendSummary(trendData);
    summary.characterId = characterId;

    // Salva/aggiorna il summary
    await prisma.trendSummary.upsert({
      where: { characterId },
      update: summary,
      create: summary
    });

    console.log(`Updated trend summary for character ${characterId}`);
  }

  /**
   * Calcola il trend summary da trend data grezzi
   */
  private calculateTrendSummary(trendData: any[]): Omit<TrendSummaryData, 'characterId'> {
    // Filtra per regioni e keyword types
    const globalCosplay = trendData.filter(t => t.region === 'GLOBAL' && t.keywordType === 'COSPLAY');
    const globalCharacter = trendData.filter(t => t.region === 'GLOBAL' && (t.keywordType === 'CHARACTER' || t.keywordType === 'GENERAL'));
    const globalShopping = trendData.filter(t => t.region === 'GLOBAL' && (t.keywordType === 'FIGURE' || t.keywordType === 'MERCH'));
    
    const usCosplay = trendData.filter(t => t.region === 'US' && t.keywordType === 'COSPLAY');
    const jpCharacter = trendData.filter(t => t.region === 'JP' && (t.keywordType === 'CHARACTER' || t.keywordType === 'GENERAL'));
    const itCosplay = trendData.filter(t => t.region === 'IT' && t.keywordType === 'COSPLAY');

    // Calcola medie ponderate (più peso ai trend recenti)
    const globalCosplayScore = this.calculateWeightedAverage(globalCosplay);
    const globalCharacterScore = this.calculateWeightedAverage(globalCharacter);
    const globalShoppingScore = this.calculateWeightedAverage(globalShopping);
    const usCosplayScore = this.calculateWeightedAverage(usCosplay);
    const jpCharacterScore = this.calculateWeightedAverage(jpCharacter);
    const itCosplayScore = this.calculateWeightedAverage(itCosplay);

    // Calcola scores complessivi
    const cosplayTrendScore = (globalCosplayScore * 0.4) + (usCosplayScore * 0.3) + (itCosplayScore * 0.3);
    const overallTrendScore = (globalCharacterScore * 0.3) + (cosplayTrendScore * 0.5) + (globalShoppingScore * 0.2);

    // Identifica mercati in crescita
    const risingMarkets = this.identifyRisingMarkets(trendData);
    const bestMarket = this.findBestMarket(trendData);

    // Calcola qualità dei dati
    const dataQuality = this.calculateDataQuality(trendData);

    return {
      globalCosplayScore,
      globalCharacterScore,
      globalShoppingScore,
      usCosplayScore,
      jpCharacterScore,
      itCosplayScore,
      overallTrendScore,
      cosplayTrendScore,
      risingMarkets,
      bestMarket,
      dataQuality
    };
  }

  /**
   * Calcola media ponderata con più peso ai trend recenti
   */
  private calculateWeightedAverage(trends: any[]): number {
    if (trends.length === 0) return 0;

    const weightedSum = trends.reduce((sum, trend) => {
      // Peso maggiore per 7d, peso medio per 30d, peso minore per 90d
      const score = (trend.trend7d * 0.5) + (trend.trend30d * 0.3) + (trend.trend90d * 0.2);
      return sum + (score * trend.confidence); // Ponderato per confidence
    }, 0);

    const totalWeight = trends.reduce((sum, trend) => sum + trend.confidence, 0);
    
    return totalWeight > 0 ? Math.round((weightedSum / totalWeight) * 100) / 100 : 0;
  }

  /**
   * Identifica mercati con trend in crescita
   */
  private identifyRisingMarkets(trendData: any[]): string[] {
    const risingMarkets: string[] = [];
    
    // Raggruppa per regione
    const regionGroups = trendData.reduce((groups, trend) => {
      if (!groups[trend.region]) groups[trend.region] = [];
      groups[trend.region].push(trend);
      return groups;
    }, {});

    // Per ogni regione, controlla se 7d > 30d (trend crescente)
    Object.entries(regionGroups).forEach(([region, trends]: [string, any[]]) => {
      const avgTrend7d = trends.reduce((sum, t) => sum + t.trend7d, 0) / trends.length;
      const avgTrend30d = trends.reduce((sum, t) => sum + t.trend30d, 0) / trends.length;
      
      if (avgTrend7d > avgTrend30d * 1.2) { // 20% di crescita
        risingMarkets.push(region);
      }
    });

    return risingMarkets;
  }

  /**
   * Trova il mercato con performance migliore
   */
  private findBestMarket(trendData: any[]): TrendRegion | null {
    const regionScores = new Map<string, number>();

    // Calcola score per regione
    trendData.forEach(trend => {
      const currentScore = regionScores.get(trend.region) || 0;
      const trendScore = (trend.trend7d * 0.5) + (trend.trend30d * 0.3) + (trend.trend90d * 0.2);
      regionScores.set(trend.region, currentScore + trendScore);
    });

    // Trova la regione con score più alto
    let bestRegion = null;
    let bestScore = 0;

    regionScores.forEach((score, region) => {
      if (score > bestScore) {
        bestScore = score;
        bestRegion = region;
      }
    });

    return bestRegion as TrendRegion | null;
  }

  /**
   * Calcola qualità dei dati (basata su coverage e confidence)
   */
  private calculateDataQuality(trendData: any[]): number {
    if (trendData.length === 0) return 0;

    // Coverage: quante regioni/keyword types abbiamo
    const uniqueRegions = new Set(trendData.map(t => t.region)).size;
    const uniqueKeywordTypes = new Set(trendData.map(t => t.keywordType)).size;
    const coverageScore = Math.min((uniqueRegions / 5) * (uniqueKeywordTypes / 3), 1); // Max 5 regioni, 3 keyword types

    // Confidence media
    const avgConfidence = trendData.reduce((sum, t) => sum + t.confidence, 0) / trendData.length;

    // Score combinato
    return Math.round(((coverageScore * 0.6) + (avgConfidence * 0.4)) * 100) / 100;
  }

  /**
   * Aggiorna trend per un batch di personaggi
   */
  async updateCharacterTrends(characterIds: string[]): Promise<{
    success: boolean;
    updated: number;
    errors: string[];
  }> {
    console.log(`Starting trend update for ${characterIds.length} characters`);
    
    const errors: string[] = [];
    let updated = 0;

    try {
      // Ottieni dati dei personaggi
      const characters = await prisma.character.findMany({
        where: {
          id: { in: characterIds }
        },
        select: {
          id: true,
          name: true,
          series: true
        }
      });

      if (characters.length === 0) {
        throw new Error('No characters found');
      }

      // Fetch trend da Google Trends (batch processing)
      const batchResults = await googleTrendsService.fetchMultipleCharacterTrends(characters, 3); // 3 per batch

      // Salva i risultati
      for (const result of batchResults) {
        try {
          if (result.trends.length > 0) {
            await this.saveTrendData(result.characterId, result.trends);
            await this.updateTrendSummary(result.characterId);
            updated++;
          }
          
          if (result.errors.length > 0) {
            errors.push(...result.errors);
          }
        } catch (error) {
          const errorMsg = `Failed to save trends for character ${result.characterId}: ${error}`;
          console.error(errorMsg);
          errors.push(errorMsg);
        }
      }

      console.log(`Trend update completed: ${updated} characters updated, ${errors.length} errors`);

      return {
        success: errors.length === 0,
        updated,
        errors
      };

    } catch (error) {
      const errorMsg = `Fatal error during trend update: ${error}`;
      console.error(errorMsg);
      errors.push(errorMsg);

      return {
        success: false,
        updated,
        errors
      };
    }
  }

  /**
   * Ottieni trend summary per personaggi con filtri
   */
  async getTrendSummaries(options: {
    limit?: number;
    sortBy?: 'overallTrendScore' | 'cosplayTrendScore' | 'globalCosplayScore';
    region?: TrendRegion;
    minScore?: number;
  } = {}) {
    const { limit = 20, sortBy = 'overallTrendScore', minScore = 0 } = options;

    const orderBy = { [sortBy]: 'desc' as const };
    
    const where: any = {};
    if (minScore > 0) {
      where[sortBy] = { gte: minScore };
    }

    return await prisma.trendSummary.findMany({
      where,
      include: {
        character: {
          select: {
            id: true,
            name: true,
            series: true,
            imageUrl: true,
            gender: true,
            source: true
          }
        }
      },
      orderBy,
      take: limit
    });
  }

  /**
   * Ottieni trend dettagliati per un personaggio
   */
  async getCharacterTrendDetails(characterId: string) {
    const [trendData, summary] = await Promise.all([
      prisma.googleTrendData.findMany({
        where: { characterId },
        orderBy: { date: 'desc' }
      }),
      prisma.trendSummary.findUnique({
        where: { characterId },
        include: {
          character: {
            select: {
              id: true,
              name: true,
              series: true,
              imageUrl: true,
              gender: true,
              source: true
            }
          }
        }
      })
    ]);

    return {
      summary,
      detailedTrends: trendData
    };
  }
}

// Export singleton instance
export const googleTrendsDbService = new GoogleTrendsDbService();
export default googleTrendsDbService;

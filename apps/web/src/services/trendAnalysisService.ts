/**
 * Trend Analysis Service
 * Analizza i trend dei personaggi e predice i breakout
 */

import { prisma } from '@cosplayradar/db';
import { simpleGoogleTrendsService } from './simpleGoogleTrendsService';

interface TrendAnalysisResult {
  characterId: string;
  isNew: boolean;
  isUpcoming: boolean;
  isTrendingUp: boolean;
  isBreakout: boolean;
  popularityScore: number;
  trendScore: number;
  momentumScore: number;
  anticipationScore: number;
  overallScore: number;
  trendDelta7d: number;
  trendDelta30d: number;
  trendCategory: string;
  breakoutPotential: string;
  confidence: number;
}

class TrendAnalysisService {

  /**
   * Analizza tutti i personaggi per trend e potenziale breakout
   */
  async analyzeAllCharacterTrends(): Promise<{
    success: boolean;
    analyzed: number;
    newBreakouts: number;
    updatedAnalyses: number;
    errors: string[];
  }> {
    console.log('🔍 Starting comprehensive trend analysis...');
    
    const result = {
      success: false,
      analyzed: 0,
      newBreakouts: 0,
      updatedAnalyses: 0,
      errors: [] as string[]
    };

    try {
      // Ottieni tutti i personaggi che necessitano di analisi
      const characters = await this.getCharactersForAnalysis();
      console.log(`📊 Found ${characters.length} characters to analyze`);

      for (const character of characters) {
        try {
          const analysis = await this.analyzeCharacterTrend(character);
          
          if (analysis) {
            const saved = await this.saveTrendAnalysis(analysis);
            
            if (saved.isNew) {
              result.newBreakouts++;
            } else {
              result.updatedAnalyses++;
            }
            
            result.analyzed++;
          }

          // Rate limiting per le API
          await new Promise(resolve => setTimeout(resolve, 1000));

        } catch (error) {
          console.error(`❌ Error analyzing character ${character.id}:`, error);
          result.errors.push(`Failed to analyze ${character.name}: ${error}`);
        }
      }

      result.success = result.errors.length < result.analyzed / 2;
      
      console.log(`✅ Analysis complete: ${result.analyzed} analyzed, ${result.newBreakouts} new breakouts`);
      return result;

    } catch (error) {
      console.error('❌ Trend analysis failed:', error);
      result.errors.push(`Analysis failed: ${error}`);
      return result;
    }
  }

  /**
   * Ottiene personaggi che necessitano di analisi
   */
  private async getCharactersForAnalysis(): Promise<any[]> {
    // Priorità ai personaggi:
    // 1. Da serie nuove o imminenti
    // 2. Con popolarità alta
    // 3. Non analizzati di recente

    return await prisma.character.findMany({
      where: {
        OR: [
          // Personaggi mai analizzati
          { trendAnalysis: null },
          // Personaggi analizzati più di 7 giorni fa
          {
            trendAnalysis: {
              lastAnalyzed: {
                lt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
              }
            }
          },
          // Personaggi da serie trending
          {
            animeReleases: {
              some: {
                OR: [
                  { isTrending: true },
                  { isUpcoming: true },
                  { isNew: true }
                ]
              }
            }
          }
        ]
      },
      include: {
        animeReleases: true,
        trendAnalysis: true,
        trends: {
          where: {
            platform: 'OTHER' // Google Trends data
          },
          orderBy: {
            date: 'desc'
          },
          take: 10
        }
      },
      orderBy: [
        { popularityScore: 'desc' },
        { updatedAt: 'desc' }
      ],
      take: 100 // Limite per evitare overload
    });
  }

  /**
   * Analizza un singolo personaggio
   */
  private async analyzeCharacterTrend(character: any): Promise<TrendAnalysisResult | null> {
    try {
      console.log(`🔍 Analyzing ${character.name}...`);

      // 1. Analizza contesto della serie
      const seriesContext = this.analyzeSeriesContext(character.animeReleases || []);
      
      // 2. Analizza trend storici Google
      const trendHistory = this.analyzeTrendHistory(character.trends || []);
      
      // 3. Calcola score di popolarità AniList
      const popularityScore = this.calculatePopularityScore(character);
      
      // 4. Ottieni trend Google recenti (simulati per ora)
      const currentTrends = await this.getCurrentTrends(character);
      
      // 5. Calcola momentum e delta
      const momentum = this.calculateMomentum(trendHistory, currentTrends);
      
      // 6. Calcola score di anticipazione
      const anticipationScore = this.calculateAnticipationScore(
        seriesContext,
        momentum,
        popularityScore
      );
      
      // 7. Classifica trend
      const classification = this.classifyTrend(momentum, anticipationScore, seriesContext);
      
      // 8. Calcola score finale
      const overallScore = this.calculateOverallScore(
        popularityScore,
        currentTrends.trendScore,
        momentum.momentumScore,
        anticipationScore
      );

      return {
        characterId: character.id,
        isNew: seriesContext.isNew,
        isUpcoming: seriesContext.isUpcoming,
        isTrendingUp: momentum.isRising,
        isBreakout: classification.isBreakout,
        popularityScore,
        trendScore: currentTrends.trendScore,
        momentumScore: momentum.momentumScore,
        anticipationScore,
        overallScore,
        trendDelta7d: momentum.delta7d,
        trendDelta30d: momentum.delta30d,
        trendCategory: classification.category,
        breakoutPotential: classification.breakoutLevel,
        confidence: this.calculateConfidence(character, trendHistory, seriesContext)
      };

    } catch (error) {
      console.error(`❌ Error in character analysis for ${character.name}:`, error);
      return null;
    }
  }

  /**
   * Analizza il contesto delle serie associate
   */
  private analyzeSeriesContext(animeReleases: any[]): {
    isNew: boolean;
    isUpcoming: boolean;
    isTrending: boolean;
    maxPopularity: number;
    averageTrendRank: number;
  } {
    if (animeReleases.length === 0) {
      return {
        isNew: false,
        isUpcoming: false,
        isTrending: false,
        maxPopularity: 0,
        averageTrendRank: 0
      };
    }

    const isNew = animeReleases.some(anime => anime.isNew);
    const isUpcoming = animeReleases.some(anime => anime.isUpcoming);
    const isTrending = animeReleases.some(anime => anime.isTrending);
    const maxPopularity = Math.max(...animeReleases.map(anime => anime.popularity || 0));
    const trendRanks = animeReleases.filter(anime => anime.trendRank).map(anime => anime.trendRank);
    const averageTrendRank = trendRanks.length > 0 ? 
      trendRanks.reduce((sum, rank) => sum + rank, 0) / trendRanks.length : 0;

    return {
      isNew,
      isUpcoming,
      isTrending,
      maxPopularity,
      averageTrendRank
    };
  }

  /**
   * Analizza storico trend Google
   */
  private analyzeTrendHistory(trends: any[]): {
    hasHistory: boolean;
    averageScore: number;
    peakScore: number;
    recentTrend: number;
    oldTrend: number;
  } {
    if (trends.length === 0) {
      return {
        hasHistory: false,
        averageScore: 0,
        peakScore: 0,
        recentTrend: 0,
        oldTrend: 0
      };
    }

    const scores = trends.map(t => t.mentions || 0);
    const averageScore = scores.reduce((sum, score) => sum + score, 0) / scores.length;
    const peakScore = Math.max(...scores);
    
    // Ultimi 3 vs precedenti per trend
    const recentScores = scores.slice(0, 3);
    const oldScores = scores.slice(3, 6);
    
    const recentTrend = recentScores.length > 0 ? 
      recentScores.reduce((sum, score) => sum + score, 0) / recentScores.length : 0;
    const oldTrend = oldScores.length > 0 ? 
      oldScores.reduce((sum, score) => sum + score, 0) / oldScores.length : 0;

    return {
      hasHistory: true,
      averageScore,
      peakScore,
      recentTrend,
      oldTrend
    };
  }

  /**
   * Calcola score di popolarità da AniList
   */
  private calculatePopularityScore(character: any): number {
    // Normalizza popularity score (0-100)
    const baseScore = Math.min(character.popularityScore || 0, 100000) / 1000;
    
    // Bonus per personaggi con anilistId (dati verificati)
    const verificationBonus = character.anilistId ? 1.2 : 1.0;
    
    // Bonus per descrizione dettagliata
    const detailBonus = character.description ? 1.1 : 1.0;
    
    return Math.min(baseScore * verificationBonus * detailBonus, 100);
  }

  /**
   * Ottiene trend Google attuali (simulati per sviluppo)
   */
  private async getCurrentTrends(character: any): Promise<{
    trendScore: number;
    confidence: number;
  }> {
    // In development, simula trend realistici
    // In produzione, usa simpleGoogleTrendsService
    
    if (process.env.NODE_ENV === 'development') {
      // Simula trend basati su popolarità
      const baseTrend = Math.min(character.popularityScore / 1000 * 100, 100);
      const randomVariation = (Math.random() - 0.5) * 20; // ±10
      const trendScore = Math.max(0, Math.min(100, baseTrend + randomVariation));
      
      return {
        trendScore,
        confidence: 0.7 + Math.random() * 0.2
      };
    }

    // Produzione: usa Google Trends reali
    try {
      const trendsResult = await simpleGoogleTrendsService.getTrendsForCharacter({
        id: character.id,
        name: character.name,
        series: character.series
      });

      if (trendsResult.trends.length > 0) {
        const cosplayTrend = trendsResult.trends.find(t => t.keywordType === 'COSPLAY');
        return {
          trendScore: cosplayTrend?.trend7d || 0,
          confidence: cosplayTrend?.confidence || 0.5
        };
      }

      return { trendScore: 0, confidence: 0.1 };

    } catch (error) {
      console.warn('⚠️  Failed to get current trends, using fallback');
      return { trendScore: 0, confidence: 0.1 };
    }
  }

  /**
   * Calcola momentum del trend
   */
  private calculateMomentum(history: any, current: any): {
    momentumScore: number;
    delta7d: number;
    delta30d: number;
    isRising: boolean;
  } {
    if (!history.hasHistory) {
      return {
        momentumScore: 0,
        delta7d: 0,
        delta30d: 0,
        isRising: false
      };
    }

    // Calcola delta percentuali
    const delta7d = history.oldTrend > 0 ? 
      ((history.recentTrend - history.oldTrend) / history.oldTrend) * 100 : 0;
    
    const delta30d = history.averageScore > 0 ? 
      ((current.trendScore - history.averageScore) / history.averageScore) * 100 : 0;

    // Score di momentum (0-100)
    const momentumScore = Math.max(0, Math.min(100, 
      (delta7d * 0.6) + (delta30d * 0.4) + 50
    ));

    const isRising = delta7d > 5 || delta30d > 10; // Crescita significativa

    return {
      momentumScore,
      delta7d,
      delta30d,
      isRising
    };
  }

  /**
   * Calcola score di anticipazione
   */
  private calculateAnticipationScore(
    seriesContext: any,
    momentum: any,
    popularityScore: number
  ): number {
    let score = 0;

    // Bonus per serie nuove/imminenti
    if (seriesContext.isNew) score += 30;
    if (seriesContext.isUpcoming) score += 25;
    if (seriesContext.isTrending) score += 20;

    // Bonus per momentum positivo
    if (momentum.isRising) score += 15;
    score += momentum.momentumScore * 0.2;

    // Bonus per popolarità base
    score += popularityScore * 0.3;

    // Bonus per ranking serie
    if (seriesContext.averageTrendRank > 0) {
      score += Math.max(0, (100 - seriesContext.averageTrendRank) * 0.1);
    }

    return Math.min(100, score);
  }

  /**
   * Classifica il trend
   */
  private classifyTrend(momentum: any, anticipationScore: number, seriesContext: any): {
    category: string;
    breakoutLevel: string;
    isBreakout: boolean;
  } {
    let category = 'STABLE';
    let breakoutLevel = 'LOW';
    let isBreakout = false;

    // Determina categoria
    if (momentum.isRising && momentum.delta7d > 20) {
      category = 'VIRAL';
    } else if (momentum.isRising && momentum.delta7d > 10) {
      category = 'RISING';
    } else if (seriesContext.isNew || seriesContext.isUpcoming) {
      category = 'EMERGING';
    } else if (momentum.delta7d < -10) {
      category = 'DECLINING';
    }

    // Determina potenziale breakout
    if (anticipationScore > 80) {
      breakoutLevel = 'IMMINENT';
      isBreakout = true;
    } else if (anticipationScore > 65) {
      breakoutLevel = 'HIGH';
      isBreakout = anticipationScore > 70;
    } else if (anticipationScore > 45) {
      breakoutLevel = 'MEDIUM';
    }

    return { category, breakoutLevel, isBreakout };
  }

  /**
   * Calcola score finale combinato
   */
  private calculateOverallScore(
    popularityScore: number,
    trendScore: number,
    momentumScore: number,
    anticipationScore: number
  ): number {
    // Weighted average con pesi strategici
    const weights = {
      popularity: 0.25,    // Popolarità base
      trend: 0.35,         // Trend attuali (più importante)
      momentum: 0.25,      // Momentum di crescita
      anticipation: 0.15   // Potenziale futuro
    };

    return Math.round(
      (popularityScore * weights.popularity) +
      (trendScore * weights.trend) +
      (momentumScore * weights.momentum) +
      (anticipationScore * weights.anticipation)
    );
  }

  /**
   * Calcola confidenza dell'analisi
   */
  private calculateConfidence(character: any, history: any, seriesContext: any): number {
    let confidence = 0.5; // Base

    // Bonus per dati verificati
    if (character.anilistId) confidence += 0.2;
    if (character.description) confidence += 0.1;

    // Bonus per storico trend
    if (history.hasHistory) confidence += 0.15;

    // Bonus per contesto serie
    if (seriesContext.maxPopularity > 1000) confidence += 0.1;

    return Math.min(1.0, confidence);
  }

  /**
   * Salva l'analisi nel database
   */
  private async saveTrendAnalysis(analysis: TrendAnalysisResult): Promise<{
    isNew: boolean;
    updated: boolean;
  }> {
    try {
      const existing = await prisma.characterTrendAnalysis.findUnique({
        where: { characterId: analysis.characterId }
      });

      const analysisData = {
        characterId: analysis.characterId,
        isNew: analysis.isNew,
        isUpcoming: analysis.isUpcoming,
        isTrendingUp: analysis.isTrendingUp,
        isBreakout: analysis.isBreakout,
        popularityScore: analysis.popularityScore,
        trendScore: analysis.trendScore,
        momentumScore: analysis.momentumScore,
        anticipationScore: analysis.anticipationScore,
        overallScore: analysis.overallScore,
        trendDelta7d: analysis.trendDelta7d,
        trendDelta30d: analysis.trendDelta30d,
        trendCategory: analysis.trendCategory as any,
        breakoutPotential: analysis.breakoutPotential as any,
        confidence: analysis.confidence,
        dataQuality: 0.8, // Default
        lastAnalyzed: new Date()
      };

      if (existing) {
        await prisma.characterTrendAnalysis.update({
          where: { characterId: analysis.characterId },
          data: analysisData
        });
        return { isNew: false, updated: true };
      } else {
        await prisma.characterTrendAnalysis.create({
          data: analysisData
        });
        return { isNew: true, updated: false };
      }

    } catch (error) {
      console.error(`❌ Error saving trend analysis:`, error);
      throw error;
    }
  }

  /**
   * Ottiene statistiche dell'analisi
   */
  async getAnalysisStats(): Promise<{
    totalAnalyzed: number;
    breakoutCandidates: number;
    risingTrends: number;
    emergingCharacters: number;
    recentlyAnalyzed: number;
  }> {
    try {
      const [total, breakouts, rising, emerging, recent] = await Promise.all([
        prisma.characterTrendAnalysis.count(),
        prisma.characterTrendAnalysis.count({ where: { isBreakout: true } }),
        prisma.characterTrendAnalysis.count({ where: { isTrendingUp: true } }),
        prisma.characterTrendAnalysis.count({ 
          where: { 
            OR: [
              { isNew: true },
              { isUpcoming: true }
            ]
          }
        }),
        prisma.characterTrendAnalysis.count({
          where: {
            lastAnalyzed: {
              gte: new Date(Date.now() - 24 * 60 * 60 * 1000)
            }
          }
        })
      ]);

      return {
        totalAnalyzed: total,
        breakoutCandidates: breakouts,
        risingTrends: rising,
        emergingCharacters: emerging,
        recentlyAnalyzed: recent
      };

    } catch (error) {
      console.error('❌ Error getting analysis stats:', error);
      return {
        totalAnalyzed: 0,
        breakoutCandidates: 0,
        risingTrends: 0,
        emergingCharacters: 0,
        recentlyAnalyzed: 0
      };
    }
  }
}

// Export singleton
export const trendAnalysisService = new TrendAnalysisService();
export default trendAnalysisService;

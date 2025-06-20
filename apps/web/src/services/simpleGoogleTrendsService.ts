/**
 * Google Trends Service Semplificato
 * Versione che bypassa i problemi di TypeScript e si concentra sulla funzionalità
 */

import googleTrends from 'google-trends-api';
import { LRUCache } from 'lru-cache';

// Cache semplice
const cache = new LRUCache<string, any>({
  max: 200,
  ttl: 1000 * 60 * 60 * 4, // 4 ore
});

let lastRequestTime = 0;
const REQUEST_DELAY = 15000; // 15 secondi tra richieste

export interface SimpleCharacter {
  id: string;
  name: string;
  series: string;
}

export interface SimpleTrendResult {
  characterId: string;
  keyword: string;
  keywordType: string;
  region: string;
  trend7d: number;
  trend30d: number;
  confidence: number;
  date: string;
}

export interface SimpleBatchResult {
  characterId: string;
  trends: SimpleTrendResult[];
  errors: string[];
}

class SimpleGoogleTrendsService {

  async getTrendsForCharacter(character: SimpleCharacter): Promise<SimpleBatchResult> {
    const results: SimpleTrendResult[] = [];
    const errors: string[] = [];

    // Keywords da testare
    const keywords = [
      { keyword: `${character.name} cosplay`, type: 'COSPLAY' },
      { keyword: character.name, type: 'CHARACTER' }
    ];

    for (const keywordData of keywords) {
      try {
        await this.enforceRateLimit();

        const cacheKey = `${character.id}-${keywordData.keyword}-GLOBAL`;
        const cached = cache.get(cacheKey);
        
        if (cached) {
          results.push({
            characterId: character.id,
            keyword: keywordData.keyword,
            keywordType: keywordData.type,
            region: 'GLOBAL',
            trend7d: cached.trend7d || 0,
            trend30d: cached.trend30d || 0,
            confidence: cached.confidence || 0.5,
            date: new Date().toISOString()
          });
          continue;
        }

        // Fetch da Google Trends
        const trendData = await this.fetchTrendData(keywordData.keyword, 'GLOBAL');
        
        const trendResult: SimpleTrendResult = {
          characterId: character.id,
          keyword: keywordData.keyword,
          keywordType: keywordData.type,
          region: 'GLOBAL',
          trend7d: trendData.trend7d,
          trend30d: trendData.trend30d,
          confidence: trendData.confidence,
          date: new Date().toISOString()
        };

        results.push(trendResult);
        cache.set(cacheKey, trendResult);

      } catch (error) {
        console.error(`Error fetching trends for ${keywordData.keyword}:`, error);
        errors.push(`Failed to fetch ${keywordData.keyword}: ${error}`);
      }
    }

    return {
      characterId: character.id,
      trends: results,
      errors
    };
  }

  async getTrendsForMultipleCharacters(characters: SimpleCharacter[]): Promise<SimpleBatchResult[]> {
    const results: SimpleBatchResult[] = [];
    
    console.log(`Fetching trends for ${characters.length} characters`);

    for (const character of characters) {
      try {
        const result = await this.getTrendsForCharacter(character);
        results.push(result);
        
        // Delay tra personaggi
        await new Promise(resolve => setTimeout(resolve, 20000)); // 20 secondi
        
      } catch (error) {
        console.error(`Failed to process ${character.name}:`, error);
        results.push({
          characterId: character.id,
          trends: [],
          errors: [`Failed to process character: ${error}`]
        });
      }
    }

    return results;
  }

  private async fetchTrendData(keyword: string, region: string): Promise<{
    trend7d: number;
    trend30d: number;
    confidence: number;
  }> {
    try {
      // Simula il fetch da Google Trends con dati mock per sviluppo
      if (process.env.NODE_ENV === 'development') {
        return {
          trend7d: Math.floor(Math.random() * 100),
          trend30d: Math.floor(Math.random() * 100),
          confidence: 0.7 + Math.random() * 0.3
        };
      }

      // Fetch reale da Google Trends
      const response = await googleTrends.interestOverTime({
        keyword: keyword,
        geo: region === 'GLOBAL' ? '' : region,
        startTime: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 giorni fa
        endTime: new Date()
      });

      const data = JSON.parse(response);
      const timelineData = data.default?.timelineData || [];

      if (timelineData.length === 0) {
        return { trend7d: 0, trend30d: 0, confidence: 0.1 };
      }

      // Calcola medie per 7d e 30d
      const recent7d = timelineData.slice(-7);
      const recent30d = timelineData;

      const trend7d = recent7d.reduce((sum: number, item: any) => sum + (item.value?.[0] || 0), 0) / recent7d.length;
      const trend30d = recent30d.reduce((sum: number, item: any) => sum + (item.value?.[0] || 0), 0) / recent30d.length;

      return {
        trend7d: Math.round(trend7d * 100) / 100,
        trend30d: Math.round(trend30d * 100) / 100,
        confidence: timelineData.length > 20 ? 0.9 : 0.6
      };

    } catch (error) {
      console.error(`Error fetching Google Trends for ${keyword}:`, error);
      return { trend7d: 0, trend30d: 0, confidence: 0.1 };
    }
  }

  private async enforceRateLimit(): Promise<void> {
    const now = Date.now();
    const timeSinceLastRequest = now - lastRequestTime;
    
    if (timeSinceLastRequest < REQUEST_DELAY) {
      const waitTime = REQUEST_DELAY - timeSinceLastRequest;
      console.log(`Rate limiting: waiting ${waitTime}ms`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    lastRequestTime = Date.now();
  }
}

// Export singleton
export const simpleGoogleTrendsService = new SimpleGoogleTrendsService();
export default simpleGoogleTrendsService;

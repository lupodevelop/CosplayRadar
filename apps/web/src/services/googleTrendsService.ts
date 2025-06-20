/**
 * Google Trends Service
 * Gestisce l'integrazione con Google Trends per trend multi-dimensionali
 */

import googleTrends from 'google-trends-api';
import { LRUCache } from 'lru-cache';

// Configurazione cache per rispettare rate limits
const cache = new LRUCache<string, any>({
  max: 500, // 500 query in cache
  ttl: 1000 * 60 * 60 * 6, // 6 ore TTL (trend non cambiano spesso)
});

// Rate limiting
let lastRequestTime = 0;
const REQUEST_DELAY = 12000; // 12 secondi tra le richieste (5 richieste/minuto)

// Configurazioni
export const TREND_REGIONS = {
  GLOBAL: '', // Globale
  US: 'US',
  JP: 'JP', 
  IT: 'IT',
  UK: 'GB',
  DE: 'DE',
  FR: 'FR',
  BR: 'BR',
  KR: 'KR',
  CA: 'CA',
  AU: 'AU',
  MX: 'MX'
} as const;

export const TREND_TIMEFRAMES = {
  '7d': 'now 7-d',
  '30d': 'today 1-m', 
  '90d': 'today 3-m'
} as const;

export type TrendRegion = keyof typeof TREND_REGIONS;
export type KeywordType = 'COSPLAY' | 'CHARACTER' | 'COSTUME' | 'FANART' | 'FIGURE' | 'MERCH' | 'GENERAL';

export interface Character {
  id: string;
  name: string;
  series: string;
}

export interface TrendKeyword {
  keyword: string;
  type: KeywordType;
}

export interface TrendResult {
  keyword: string;
  keywordType: KeywordType;
  region: TrendRegion;
  trend7d: number;
  trend30d: number;
  trend90d: number;
  confidence: number;
  queryVolume: 'LOW' | 'MEDIUM' | 'HIGH' | 'VIRAL';
}

export interface BatchTrendResult {
  characterId: string;
  trends: TrendResult[];
  errors: string[];
}

class GoogleTrendsService {
  
  /**
   * Genera keyword intelligenti per un personaggio
   */
  generateKeywords(character: Character): TrendKeyword[] {
    const keywords: TrendKeyword[] = [];
    
    // Pulisci il nome (rimuovi caratteri speciali)
    const cleanName = character.name.replace(/[^\w\s]/g, '').trim();
    const cleanSeries = character.series.replace(/[^\w\s]/g, '').trim();
    
    // COSPLAY keywords (priorità alta per creator)
    keywords.push(
      { keyword: `${cleanName} cosplay`, type: 'COSPLAY' },
      { keyword: `${cleanSeries} ${cleanName} cosplay`, type: 'COSPLAY' },
      { keyword: `${cleanName} costume`, type: 'COSTUME' }
    );
    
    // CHARACTER keywords (interesse generale)
    keywords.push(
      { keyword: cleanName, type: 'GENERAL' },
      { keyword: `${cleanName} ${cleanSeries}`, type: 'CHARACTER' },
      { keyword: `${cleanName} anime`, type: 'CHARACTER' }
    );
    
    // CONTENT/SHOPPING keywords
    keywords.push(
      { keyword: `${cleanName} fanart`, type: 'FANART' },
      { keyword: `${cleanName} figure`, type: 'FIGURE' },
      { keyword: `${cleanName} merchandise`, type: 'MERCH' }
    );
    
    return keywords;
  }

  /**
   * Rate limiting per rispettare i limiti di Google Trends
   */
  private async rateLimitDelay(): Promise<void> {
    const now = Date.now();
    const timeSinceLastRequest = now - lastRequestTime;
    
    if (timeSinceLastRequest < REQUEST_DELAY) {
      const waitTime = REQUEST_DELAY - timeSinceLastRequest;
      console.log(`Rate limiting: waiting ${waitTime}ms...`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    lastRequestTime = Date.now();
  }

  /**
   * Fetch trend per una singola keyword in una regione
   */
  async fetchKeywordTrend(
    keyword: string, 
    region: TrendRegion,
    timeframe: keyof typeof TREND_TIMEFRAMES
  ): Promise<number> {
    const cacheKey = `${keyword}-${region}-${timeframe}`;
    
    // Check cache
    const cached = cache.get(cacheKey);
    if (cached !== undefined) {
      console.log(`Cache hit for: ${cacheKey}`);
      return cached;
    }

    await this.rateLimitDelay();

    try {
      console.log(`Fetching Google Trends: "${keyword}" in ${region || 'GLOBAL'} for ${timeframe}`);
      
      const options: any = {
        keyword,
        startTime: new Date(Date.now() - (timeframe === '7d' ? 7 : timeframe === '30d' ? 30 : 90) * 24 * 60 * 60 * 1000),
        endTime: new Date(),
        granularTimeUnit: 'day'
      };
      
      if (region && TREND_REGIONS[region]) {
        options.geo = TREND_REGIONS[region];
      }

      const results = await googleTrends.interestOverTime(options);
      const data = JSON.parse(results);
      
      if (!data.default?.timelineData || data.default.timelineData.length === 0) {
        console.log(`No trend data for: ${keyword} in ${region}`);
        cache.set(cacheKey, 0);
        return 0;
      }

      // Calcola il trend medio degli ultimi giorni
      const recentData = data.default.timelineData.slice(-7); // Ultimi 7 punti dati
      const avgTrend = recentData.reduce((sum: number, point: any) => {
        return sum + (point.value?.[0] || 0);
      }, 0) / recentData.length;

      const trendScore = Math.round(avgTrend * 100) / 100; // Arrotonda a 2 decimali
      
      // Cache risultato
      cache.set(cacheKey, trendScore);
      
      console.log(`Trend for "${keyword}" in ${region}: ${trendScore}`);
      return trendScore;
      
    } catch (error) {
      console.error(`Error fetching trend for "${keyword}" in ${region}:`, error);
      cache.set(cacheKey, 0); // Cache anche errori per evitare retry continui
      return 0;
    }
  }

  /**
   * Determina il volume di query basato sul trend score
   */
  private determineQueryVolume(trendScore: number): 'LOW' | 'MEDIUM' | 'HIGH' | 'VIRAL' {
    if (trendScore >= 80) return 'VIRAL';
    if (trendScore >= 50) return 'HIGH';
    if (trendScore >= 20) return 'MEDIUM';
    return 'LOW';
  }

  /**
   * Calcola confidence basato su consistenza dei dati
   */
  private calculateConfidence(trend7d: number, trend30d: number, trend90d: number): number {
    // Se tutti i trend sono 0, bassa confidence
    if (trend7d === 0 && trend30d === 0 && trend90d === 0) return 0.1;
    
    // Se c'è consistenza tra i timeframes, alta confidence
    const variance = Math.abs(trend7d - trend30d) + Math.abs(trend30d - trend90d);
    if (variance < 10) return 0.9;
    if (variance < 25) return 0.7;
    if (variance < 50) return 0.5;
    return 0.3;
  }

  /**
   * Fetch trend completi per una keyword in tutte le regioni
   */
  async fetchKeywordTrendAllRegions(
    keyword: string,
    keywordType: KeywordType
  ): Promise<TrendResult[]> {
    const results: TrendResult[] = [];
    const errors: string[] = [];

    // Fetch per ogni regione
    for (const [regionKey, regionCode] of Object.entries(TREND_REGIONS)) {
      try {
        const trend7d = await this.fetchKeywordTrend(keyword, regionKey as TrendRegion, '7d');
        const trend30d = await this.fetchKeywordTrend(keyword, regionKey as TrendRegion, '30d');
        const trend90d = await this.fetchKeywordTrend(keyword, regionKey as TrendRegion, '90d');
        
        const confidence = this.calculateConfidence(trend7d, trend30d, trend90d);
        const queryVolume = this.determineQueryVolume(Math.max(trend7d, trend30d, trend90d));

        results.push({
          keyword,
          keywordType,
          region: regionKey as TrendRegion,
          trend7d,
          trend30d,
          trend90d,
          confidence,
          queryVolume
        });

        // Delay tra regioni per rate limiting
        await new Promise(resolve => setTimeout(resolve, 1000));
        
      } catch (error) {
        const errorMsg = `Failed to fetch ${keyword} trends for ${regionKey}: ${error}`;
        console.error(errorMsg);
        errors.push(errorMsg);
      }
    }

    return results;
  }

  /**
   * Fetch trend completi per un personaggio (tutte le keyword, tutte le regioni)
   */
  async fetchCharacterTrends(character: Character): Promise<BatchTrendResult> {
    console.log(`Starting trend fetch for character: ${character.name}`);
    
    const keywords = this.generateKeywords(character);
    const allTrends: TrendResult[] = [];
    const errors: string[] = [];

    // Processa 2-3 keyword più importanti per non superare rate limits
    const priorityKeywords = keywords.filter(k => 
      k.type === 'COSPLAY' || k.type === 'CHARACTER' || k.type === 'GENERAL'
    ).slice(0, 3);

    for (const keywordObj of priorityKeywords) {
      try {
        console.log(`Processing keyword: ${keywordObj.keyword} (${keywordObj.type})`);
        
        const trends = await this.fetchKeywordTrendAllRegions(keywordObj.keyword, keywordObj.type);
        allTrends.push(...trends);
        
        // Delay significativo tra keyword per rate limiting
        await new Promise(resolve => setTimeout(resolve, 5000));
        
      } catch (error) {
        const errorMsg = `Failed to process keyword ${keywordObj.keyword}: ${error}`;
        console.error(errorMsg);
        errors.push(errorMsg);
      }
    }

    console.log(`Completed trend fetch for ${character.name}: ${allTrends.length} trend data points`);

    return {
      characterId: character.id,
      trends: allTrends,
      errors
    };
  }

  /**
   * Batch processing per più personaggi con rate limiting appropriato
   */
  async fetchMultipleCharacterTrends(
    characters: Character[],
    maxBatchSize = 5 // Massimo 5 personaggi per batch per rispettare rate limits
  ): Promise<BatchTrendResult[]> {
    const results: BatchTrendResult[] = [];
    
    console.log(`Starting batch trend fetch for ${characters.length} characters`);
    
    // Processa in batch piccoli
    for (let i = 0; i < characters.length; i += maxBatchSize) {
      const batch = characters.slice(i, i + maxBatchSize);
      
      console.log(`Processing batch ${Math.floor(i/maxBatchSize) + 1}/${Math.ceil(characters.length/maxBatchSize)}`);
      
      for (const character of batch) {
        try {
          const result = await this.fetchCharacterTrends(character);
          results.push(result);
          
          // Delay significativo tra personaggi
          await new Promise(resolve => setTimeout(resolve, 30000)); // 30 secondi
          
        } catch (error) {
          console.error(`Failed to fetch trends for ${character.name}:`, error);
          results.push({
            characterId: character.id,
            trends: [],
            errors: [`Failed to fetch trends: ${error}`]
          });
        }
      }
      
      // Delay tra batch
      if (i + maxBatchSize < characters.length) {
        console.log('Waiting 2 minutes before next batch...');
        await new Promise(resolve => setTimeout(resolve, 120000)); // 2 minuti
      }
    }

    console.log(`Completed batch processing: ${results.length} characters processed`);
    return results;
  }
}

// Export singleton instance
export const googleTrendsService = new GoogleTrendsService();
export default googleTrendsService;

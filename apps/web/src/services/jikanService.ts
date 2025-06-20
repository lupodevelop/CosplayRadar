/**
 * Jikan API Service
 * Integrazione con l'API ufficiale di MyAnimeList tramite Jikan v4
 * https://jikan.moe/
 */

import axios from 'axios';
import { LRUCache } from 'lru-cache';

// Cache configuration
const cache = new LRUCache<string, any>({
  max: 100, // massimo 100 elementi in cache
  ttl: 1000 * 60 * 15, // TTL di 15 minuti
});

// Jikan API configuration
const JIKAN_API_BASE = 'https://api.jikan.moe/v4';
const REQUEST_DELAY = 1000; // 1 secondo tra le richieste per rispettare i rate limits

// Types
export interface JikanCharacter {
  mal_id: number;
  url: string;
  images: {
    jpg: {
      image_url: string;
    };
    webp: {
      image_url: string;
    };
  };
  name: string;
  name_kanji?: string;
  nicknames: string[];
  favorites: number;
  about?: string;
  anime: Array<{
    role: string;
    anime: {
      mal_id: number;
      url: string;
      images: {
        jpg: {
          image_url: string;
        };
      };
      title: string;
    };
  }>;
  manga: Array<{
    role: string;
    manga: {
      mal_id: number;
      url: string;
      images: {
        jpg: {
          image_url: string;
        };
      };
      title: string;
    };
  }>;
  voices: any[];
}

export interface JikanTopCharactersResponse {
  data: JikanCharacter[];
  pagination: {
    last_visible_page: number;
    has_next_page: boolean;
    current_page: number;
    items: {
      count: number;
      total: number;
      per_page: number;
    };
  };
}

export interface NormalizedCharacter {
  id: string; // Useremo mal_id come identificatore
  name: string;
  imageUrl: string;
  favorites: number;
  popularity: number; // Calcolato dai favorites
  series: string; // Primo anime/manga associato
  category: 'ANIME' | 'MANGA' | 'OTHER';
  description?: string;
  tags: string[];
  fandom?: string;
  gender?: string;
  popularityScore: number;
  sourceUrl: string;
  malId: number;
  appearances: {
    anime: string[];
    manga: string[];
  };
}

class JikanService {
  private lastRequestTime = 0;

  /**
   * Implementa rate limiting per rispettare i limiti di Jikan API
   */
  private async rateLimitDelay(): Promise<void> {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;
    
    if (timeSinceLastRequest < REQUEST_DELAY) {
      const waitTime = REQUEST_DELAY - timeSinceLastRequest;
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    this.lastRequestTime = Date.now();
  }

  /**
   * Ottiene i personaggi più popolari da Jikan API
   */
  async getTopCharacters({ page = 1 }: { page?: number } = {}): Promise<{
    characters: NormalizedCharacter[];
    pagination: {
      currentPage: number;
      hasNextPage: boolean;
      totalPages: number;
    };
  }> {
    const cacheKey = `top-characters-page-${page}`;
    
    // Controlla cache
    const cached = cache.get(cacheKey);
    if (cached) {
      console.log(`Cache hit for ${cacheKey}`);
      return cached;
    }

    try {
      await this.rateLimitDelay();
      
      console.log(`Fetching top characters page ${page} from Jikan API...`);
      
      const response = await axios.get<JikanTopCharactersResponse>(
        `${JIKAN_API_BASE}/top/characters`,
        {
          params: { page },
          timeout: 10000,
        }
      );

      if (!response.data || !response.data.data) {
        throw new Error('Invalid response from Jikan API');
      }

      const normalizedCharacters = response.data.data.map(char => this.normalizeCharacter(char));
      
      const result = {
        characters: normalizedCharacters,
        pagination: {
          currentPage: response.data.pagination.current_page,
          hasNextPage: response.data.pagination.has_next_page,
          totalPages: response.data.pagination.last_visible_page,
        },
      };

      // Salva in cache
      cache.set(cacheKey, result);
      
      console.log(`Fetched ${normalizedCharacters.length} characters from page ${page}`);
      
      return result;
    } catch (error) {
      console.error('Error fetching top characters:', error);
      
      if (axios.isAxiosError(error)) {
        if (error.response?.status === 429) {
          throw new Error('Rate limit exceeded. Please try again later.');
        }
        if (error.response && error.response.status >= 500) {
          throw new Error('Jikan API server error. Please try again later.');
        }
      }
      
      throw new Error('Failed to fetch characters from Jikan API');
    }
  }

  /**
   * Ottiene dettagli di un singolo personaggio
   */
  async getCharacterById(id: number): Promise<NormalizedCharacter | null> {
    const cacheKey = `character-${id}`;
    
    const cached = cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      await this.rateLimitDelay();
      
      const response = await axios.get<{ data: JikanCharacter }>(
        `${JIKAN_API_BASE}/characters/${id}`
      );

      if (!response.data?.data) {
        return null;
      }

      const normalized = this.normalizeCharacter(response.data.data);
      cache.set(cacheKey, normalized);
      
      return normalized;
    } catch (error) {
      console.error(`Error fetching character ${id}:`, error);
      return null;
    }
  }

  /**
   * Cerca personaggi per nome
   */
  async searchCharacters(query: string, page = 1): Promise<{
    characters: NormalizedCharacter[];
    pagination: any;
  }> {
    const cacheKey = `search-${query}-page-${page}`;
    
    const cached = cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      await this.rateLimitDelay();
      
      const response = await axios.get(`${JIKAN_API_BASE}/characters`, {
        params: {
          q: query,
          page,
          limit: 25,
        },
      });

      const normalizedCharacters = response.data.data.map(this.normalizeCharacter);
      
      const result = {
        characters: normalizedCharacters,
        pagination: response.data.pagination,
      };

      cache.set(cacheKey, result);
      return result;
    } catch (error) {
      console.error('Error searching characters:', error);
      throw new Error('Failed to search characters');
    }
  }

  /**
   * Ottiene personaggi da anime recenti e popolari (ultimi 2 anni)
   */
  async getRecentTrendingCharacters({ page = 1 }: { page?: number } = {}): Promise<{
    characters: NormalizedCharacter[];
    pagination: {
      currentPage: number;
      hasNextPage: boolean;
      totalPages: number;
    };
  }> {
    const cacheKey = `recent-trending-characters-page-${page}`;
    
    // Controlla cache
    const cached = cache.get(cacheKey);
    if (cached) {
      console.log(`Cache hit for ${cacheKey}`);
      return cached;
    }

    try {
      console.log(`Fetching recent trending characters page ${page}...`);
      
      const characters: NormalizedCharacter[] = [];
      
      // Ottieni anime delle ultime stagioni (2024 e 2023)
      const seasons = [
        { year: 2024, season: 'fall' },
        { year: 2024, season: 'summer' },
        { year: 2024, season: 'spring' },
        { year: 2023, season: 'fall' },
        { year: 2023, season: 'summer' },
      ];
      
      for (const { year, season } of seasons.slice(0, 3)) { // Solo le prime 3 stagioni per evitare troppe chiamate
        try {
          await this.rateLimitDelay();
          
          console.log(`Fetching anime from ${season} ${year}...`);
          
          const seasonResponse = await axios.get(
            `https://api.jikan.moe/v4/seasons/${year}/${season}`,
            {
              params: { limit: 8 },
              timeout: 10000,
            }
          );

          if (!seasonResponse.data?.data) continue;
          
          // Prendi i 4 anime più popolari della stagione
          const popularAnime = seasonResponse.data.data
            .filter((anime: any) => anime.members > 50000) // Solo anime con buon seguito
            .sort((a: any, b: any) => (a.popularity || 9999) - (b.popularity || 9999))
            .slice(0, 4);
          
          // Per ogni anime, ottieni alcuni personaggi
          for (const anime of popularAnime) {
            try {
              await this.rateLimitDelay();
              
              const charactersResponse = await axios.get(
                `https://api.jikan.moe/v4/anime/${anime.mal_id}/characters`
              );
              
              if (charactersResponse.data?.data) {
                // Prendi i primi 2-3 personaggi (main e alcuni supporting)
                const animeCharacters = charactersResponse.data.data
                  .filter((char: any) => char.role === 'Main' || char.role === 'Supporting')
                  .slice(0, 3);
                
                for (const charData of animeCharacters) {
                  const character = charData.character;
                  
                  // Usa la popolarità dell'anime come base per il personaggio
                  const estimatedFavorites = Math.floor((anime.members || 0) / 100) + (character.favorites || 0);
                  const popularityScore = (anime.members || 0) / 1000;
                  
                  const normalized: NormalizedCharacter = {
                    id: `recent-${character.mal_id}`,
                    name: character.name,
                    imageUrl: character.images?.jpg?.image_url || '',
                    favorites: estimatedFavorites,
                    popularity: estimatedFavorites,
                    series: anime.title,
                    category: 'ANIME',
                    description: `${charData.role} character from ${anime.title} (${season} ${year})`,
                    tags: [anime.title, `${season} ${year}`, 'Recent Anime', charData.role],
                    fandom: 'Anime',
                    gender: 'Unknown',
                    popularityScore,
                    sourceUrl: character.url,
                    malId: character.mal_id,
                    appearances: {
                      anime: [anime.title],
                      manga: [],
                    },
                  };
                  
                  characters.push(normalized);
                }
              }
            } catch (error) {
              console.error(`Error fetching characters for anime ${anime.title}:`, error);
              // Continua con il prossimo anime
            }
          }
        } catch (error) {
          console.error(`Error fetching ${season} ${year} anime:`, error);
          // Continua con la prossima stagione
        }
      }

      // Ordina per popularityScore
      characters.sort((a, b) => b.popularityScore - a.popularityScore);

      const result = {
        characters: characters.slice(0, 25), // Limita a 25 per pagina
        pagination: {
          currentPage: page,
          hasNextPage: characters.length > 25,
          totalPages: Math.ceil(characters.length / 25),
        },
      };

      // Salva in cache
      cache.set(cacheKey, result);
      
      console.log(`Fetched ${characters.length} recent trending characters`);
      
      return result;
    } catch (error) {
      console.error('Error fetching recent trending characters:', error);
      throw new Error('Failed to fetch recent trending characters from Jikan API');
    }
  }

  /**
   * Ottiene personaggi dalla stagione attuale
   */
  async getCurrentSeasonCharacters(): Promise<NormalizedCharacter[]> {
    const cacheKey = 'current-season-characters';
    
    const cached = cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      await this.rateLimitDelay();
      
      console.log('Fetching current season anime...');
      
      const seasonResponse = await axios.get('https://api.jikan.moe/v4/seasons/now', {
        params: { limit: 10 },
        timeout: 10000,
      });

      if (!seasonResponse.data?.data) {
        return [];
      }

      const characters: NormalizedCharacter[] = [];
      
      // Per ogni anime della stagione corrente, ottieni alcuni personaggi
      for (const anime of seasonResponse.data.data.slice(0, 8)) {
        try {
          await this.rateLimitDelay();
          
          const charactersResponse = await axios.get(
            `https://api.jikan.moe/v4/anime/${anime.mal_id}/characters`
          );
          
          if (charactersResponse.data?.data) {
            // Prendi 1-2 personaggi principali per anime
            const mainCharacters = charactersResponse.data.data
              .filter((char: any) => char.role === 'Main')
              .slice(0, 2);
            
            for (const charData of mainCharacters) {
              const character = charData.character;
              
              const normalized: NormalizedCharacter = {
                id: `season-${character.mal_id}`,
                name: character.name,
                imageUrl: character.images?.jpg?.image_url || '',
                favorites: character.favorites || 0,
                popularity: anime.popularity || 0,
                series: anime.title,
                category: 'ANIME',
                description: `From ${anime.title} (${anime.season} ${anime.year})`,
                tags: [anime.title, `${anime.season} ${anime.year}`, 'Current Season'],
                fandom: 'Anime',
                gender: 'Unknown',
                popularityScore: (anime.members || 0) / 1000,
                sourceUrl: character.url,
                malId: character.mal_id,
                appearances: {
                  anime: [anime.title],
                  manga: [],
                },
              };
              
              characters.push(normalized);
            }
          }
        } catch (error) {
          console.error(`Error fetching characters for anime ${anime.title}:`, error);
          // Continua con il prossimo anime
        }
      }

      cache.set(cacheKey, characters);
      console.log(`Fetched ${characters.length} current season characters`);
      
      return characters;
    } catch (error) {
      console.error('Error fetching current season characters:', error);
      return [];
    }
  }

  /**
   * Ottiene un mix di personaggi trending e della stagione corrente
   */
  async getMixedTrendingCharacters({ page = 1 }: { page?: number } = {}): Promise<{
    characters: NormalizedCharacter[];
    pagination: {
      currentPage: number;
      hasNextPage: boolean;
      totalPages: number;
    };
  }> {
    try {
      console.log('Fetching mixed trending characters...');
      
      // Usa principalmente i personaggi recenti
      return await this.getRecentTrendingCharacters({ page });
    } catch (error) {
      console.error('Error fetching mixed trending characters:', error);
      // Fallback ai personaggi top normali
      return this.getTopCharacters({ page });
    }
  }

  /**
   * Normalizza un personaggio Jikan nel formato del nostro database
   */
  private normalizeCharacter(character: JikanCharacter): NormalizedCharacter {
    // Determina la serie principale (primo anime o manga)
    const primaryAnime = character.anime?.[0]?.anime?.title;
    const primaryManga = character.manga?.[0]?.manga?.title;
    const series = primaryAnime || primaryManga || 'Unknown';

    // Determina la categoria
    let category: 'ANIME' | 'MANGA' | 'OTHER' = 'OTHER';
    if (character.anime?.length > 0) {
      category = 'ANIME';
    } else if (character.manga?.length > 0) {
      category = 'MANGA';
    }

    // Calcola popularity score (normalizzato)
    const popularityScore = Math.min(character.favorites / 100, 1000); // Max 1000

    // Estrai tags dai nicknames e ruoli
    const tags = [
      ...character.nicknames,
      ...(character.anime?.map(a => a.anime.title) || []),
      ...(character.manga?.map(m => m.manga.title) || []),
    ].filter(Boolean).slice(0, 10); // Massimo 10 tags

    // Cerca di determinare il genere dall'about text (basic heuristic)
    const gender = this.extractGender(character.about || '');

    return {
      id: character.mal_id.toString(),
      name: character.name,
      imageUrl: character.images.jpg.image_url,
      favorites: character.favorites,
      popularity: character.favorites,
      series,
      category,
      description: character.about?.substring(0, 500), // Limita descrizione
      tags,
      fandom: category === 'ANIME' ? 'Anime' : category === 'MANGA' ? 'Manga' : 'Other',
      gender,
      popularityScore,
      sourceUrl: character.url,
      malId: character.mal_id,
      appearances: {
        anime: character.anime?.map(a => a.anime.title) || [],
        manga: character.manga?.map(m => m.manga.title) || [],
      },
    };
  }

  /**
   * Estrae il genere dal testo about (euristica semplice)
   */
  private extractGender(about: string): string {
    const text = about.toLowerCase();
    
    if (text.includes(' he ') || text.includes(' his ') || text.includes(' him ')) {
      return 'Male';
    }
    if (text.includes(' she ') || text.includes(' her ') || text.includes(' hers ')) {
      return 'Female';
    }
    
    return 'Unknown';
  }

  /**
   * Pulisce la cache
   */
  clearCache(): void {
    cache.clear();
    console.log('Jikan service cache cleared');
  }

  /**
   * Ottiene statistiche della cache
   */
  getCacheStats() {
    return {
      size: cache.size,
      max: cache.max,
      calculatedSize: cache.calculatedSize,
    };
  }
}

// Export singleton instance
export const jikanService = new JikanService();
export default jikanService;

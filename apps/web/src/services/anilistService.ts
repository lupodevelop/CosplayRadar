/**
 * AniList API Service
 * Integrazione con l'API GraphQL di AniList per ottenere personaggi con dati completi
 * https://anilist.gitbook.io/anilist-apiv2-docs/
 */

import { LRUCache } from 'lru-cache';

// Cache configuration
const cache = new LRUCache<string, any>({
  max: 200, // massimo 200 elementi in cache
  ttl: 1000 * 60 * 30, // TTL di 30 minuti per AniList (rate limit più generoso)
});

// AniList API configuration
const ANILIST_API_URL = 'https://graphql.anilist.co';
const REQUEST_DELAY = 500; // 500ms tra le richieste (AniList è più permissivo)

// Types
export interface AniListCharacter {
  id: number;
  name: {
    full: string;
    native?: string;
    alternative?: string[];
  };
  image: {
    large: string;
    medium: string;
  };
  description?: string;
  gender?: string;
  age?: string;
  favourites: number;
  siteUrl: string;
  media: {
    edges: Array<{
      node: {
        id: number;
        title: {
          romaji: string;
          english?: string;
          native: string;
        };
        type: 'ANIME' | 'MANGA';
        format: string;
        popularity: number;
        favourites: number;
      };
      characterRole: 'MAIN' | 'SUPPORTING' | 'BACKGROUND';
    }>;
  };
}

export interface AniListResponse<T> {
  data: T;
  errors?: Array<{
    message: string;
    status: number;
  }>;
}

export interface NormalizedAniListCharacter {
  id: string;
  name: string;
  imageUrl: string;
  favorites: number;
  popularity: number;
  series: string;
  media_title: string;
  category: 'ANIME' | 'MANGA' | 'OTHER';
  description?: string;
  tags: string[];
  fandom?: string;
  gender?: string;
  popularityScore: number;
  sourceUrl: string;
  anilistId: number;
  source: 'anilist';
  appearances: {
    anime: string[];
    manga: string[];
  };
}

class AniListService {
  private lastRequestTime = 0;

  /**
   * Implementa rate limiting per rispettare i limiti di AniList API
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
   * Esegue una query GraphQL verso AniList
   */
  private async executeGraphQLQuery<T>(query: string, variables: any = {}): Promise<T> {
    await this.rateLimitDelay();

    const response = await fetch(ANILIST_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        variables,
      }),
    });

    if (!response.ok) {
      throw new Error(`AniList API error: ${response.status} ${response.statusText}`);
    }

    const data: AniListResponse<T> = await response.json();

    if (data.errors && data.errors.length > 0) {
      throw new Error(`AniList GraphQL error: ${data.errors[0].message}`);
    }

    return data.data;
  }

  /**
   * Ottiene i personaggi più popolari della settimana
   */
  async getTopCharacters({
    gender,
    page = 1,
    perPage = 25,
  }: {
    gender?: 'Male' | 'Female' | 'Non-binary';
    page?: number;
    perPage?: number;
  } = {}): Promise<{
    characters: NormalizedAniListCharacter[];
    pagination: {
      currentPage: number;
      hasNextPage: boolean;
      total: number;
      perPage: number;
    };
  }> {
    const cacheKey = `anilist-top-characters-${gender || 'all'}-${page}-${perPage}`;
    
    // Controlla cache
    const cached = cache.get(cacheKey);
    if (cached) {
      console.log(`AniList cache hit for ${cacheKey}`);
      return cached;
    }

    const query = `
      query GetTopCharacters($page: Int, $perPage: Int) {
        Page(page: $page, perPage: $perPage) {
          pageInfo {
            currentPage
            hasNextPage
            total
            perPage
          }
          characters(sort: FAVOURITES_DESC) {
            id
            name {
              full
              native
              alternative
            }
            image {
              large
              medium
            }
            description
            gender
            age
            favourites
            siteUrl
            media(page: 1, perPage: 5, sort: POPULARITY_DESC) {
              edges {
                node {
                  id
                  title {
                    romaji
                    english
                    native
                  }
                  type
                  format
                  popularity
                  favourites
                }
                characterRole
              }
            }
          }
        }
      }
    `;

    try {
      console.log(`Fetching AniList characters page ${page} (gender: ${gender || 'all'})...`);
      
      // Prepara le variabili (rimuoviamo il filtro gender per ora)
      const variables: any = { page, perPage };
      
      const data = await this.executeGraphQLQuery<{
        Page: {
          pageInfo: {
            currentPage: number;
            hasNextPage: boolean;
            total: number;
            perPage: number;
          };
          characters: AniListCharacter[];
        };
      }>(query, variables);

      const normalizedCharacters = data.Page.characters.map(char => 
        this.normalizeCharacter(char)
      );

      const result = {
        characters: normalizedCharacters,
        pagination: data.Page.pageInfo,
      };

      // Salva in cache
      cache.set(cacheKey, result);
      
      console.log(`Fetched ${normalizedCharacters.length} AniList characters from page ${page}`);
      
      return result;
    } catch (error) {
      console.error('Error fetching AniList characters:', error);
      throw new Error(`Failed to fetch characters from AniList: ${error}`);
    }
  }

  /**
   * Ottiene personaggi trending settimanali da anime popolari recenti
   */
  async getWeeklyTrendingCharacters({
    page = 1,
    perPage = 25,
  }: {
    page?: number;
    perPage?: number;
  } = {}): Promise<{
    characters: NormalizedAniListCharacter[];
    pagination: {
      currentPage: number;
      hasNextPage: boolean;
      total: number;
      perPage: number;
    };
  }> {
    const cacheKey = `anilist-weekly-trending-${page}-${perPage}`;
    
    // Controlla cache
    const cached = cache.get(cacheKey);
    if (cached) {
      console.log(`AniList weekly trending cache hit for ${cacheKey}`);
      return cached;
    }

    // Prima ottieni gli anime trending della settimana
    const trendingAnimeQuery = `
      query GetTrendingAnime($page: Int, $perPage: Int) {
        Page(page: 1, perPage: 10) {
          media(type: ANIME, sort: TRENDING_DESC) {
            id
            title {
              romaji
              english
              native
            }
            popularity
            favourites
            trending
            characters(page: 1, perPage: 5, sort: FAVOURITES_DESC) {
              edges {
                node {
                  id
                  name {
                    full
                    native
                    alternative
                  }
                  image {
                    large
                    medium
                  }
                  description
                  gender
                  age
                  favourites
                  siteUrl
                }
                characterRole
              }
            }
          }
        }
      }
    `;

    try {
      console.log(`Fetching AniList weekly trending characters...`);
      
      const data = await this.executeGraphQLQuery<{
        Page: {
          media: Array<{
            id: number;
            title: {
              romaji: string;
              english?: string;
              native: string;
            };
            popularity: number;
            favourites: number;
            trending: number;
            characters: {
              edges: Array<{
                node: AniListCharacter;
                characterRole: 'MAIN' | 'SUPPORTING' | 'BACKGROUND';
              }>;
            };
          }>;
        };
      }>(trendingAnimeQuery, {});

      // Estrai personaggi da anime trending
      const allCharacters: NormalizedAniListCharacter[] = [];
      
      for (const anime of data.Page.media) {
        for (const charEdge of anime.characters.edges) {
          // Aggiungi il contesto dell'anime al personaggio
          const enhancedCharacter: AniListCharacter = {
            ...charEdge.node,
            media: {
              edges: [{
                node: {
                  id: anime.id,
                  title: anime.title,
                  type: 'ANIME' as const,
                  format: 'TV',
                  popularity: anime.popularity,
                  favourites: anime.favourites,
                },
                characterRole: charEdge.characterRole,
              }],
            },
          };
          
          const normalized = this.normalizeCharacter(enhancedCharacter);
          // Boost per personaggi da anime trending
          normalized.popularityScore += anime.trending * 0.1;
          allCharacters.push(normalized);
        }
      }

      // Rimuovi duplicati e ordina per popularityScore
      const uniqueCharacters = allCharacters.filter((char, index, self) => 
        self.findIndex(c => c.anilistId === char.anilistId) === index
      );
      
      uniqueCharacters.sort((a, b) => b.popularityScore - a.popularityScore);

      // Paginazione manuale
      const startIndex = (page - 1) * perPage;
      const endIndex = startIndex + perPage;
      const paginatedCharacters = uniqueCharacters.slice(startIndex, endIndex);

      const result = {
        characters: paginatedCharacters,
        pagination: {
          currentPage: page,
          hasNextPage: endIndex < uniqueCharacters.length,
          total: uniqueCharacters.length,
          perPage,
        },
      };

      // Salva in cache
      cache.set(cacheKey, result);
      
      console.log(`Fetched ${paginatedCharacters.length} weekly trending characters`);
      
      return result;
    } catch (error) {
      console.error('Error fetching weekly trending characters:', error);
      throw new Error(`Failed to fetch weekly trending characters: ${error}`);
    }
  }

  /**
   * Cerca personaggi per nome
   */
  async searchCharacters(
    name: string,
    page = 1,
    perPage = 25
  ): Promise<{
    characters: NormalizedAniListCharacter[];
    pagination: any;
  }> {
    const cacheKey = `anilist-search-${name}-${page}-${perPage}`;
    
    const cached = cache.get(cacheKey);
    if (cached) {
      return cached;
    }

    const query = `
      query SearchCharacters($name: String, $page: Int, $perPage: Int) {
        Page(page: $page, perPage: $perPage) {
          pageInfo {
            currentPage
            hasNextPage
            total
            perPage
          }
          characters(search: $name, sort: FAVOURITES_DESC) {
            id
            name {
              full
              native
              alternative
            }
            image {
              large
              medium
            }
            description
            gender
            age
            favourites
            siteUrl
            media(page: 1, perPage: 3, sort: POPULARITY_DESC) {
              edges {
                node {
                  id
                  title {
                    romaji
                    english
                    native
                  }
                  type
                  format
                  popularity
                  favourites
                }
                characterRole
              }
            }
          }
        }
      }
    `;

    try {
      const data = await this.executeGraphQLQuery<{
        Page: {
          pageInfo: any;
          characters: AniListCharacter[];
        };
      }>(query, { name, page, perPage });

      const normalizedCharacters = data.Page.characters.map(char => 
        this.normalizeCharacter(char)
      );

      const result = {
        characters: normalizedCharacters,
        pagination: data.Page.pageInfo,
      };

      cache.set(cacheKey, result);
      return result;
    } catch (error) {
      console.error('Error searching AniList characters:', error);
      throw new Error('Failed to search characters');
    }
  }

  /**
   * Normalizza un personaggio AniList nel formato del nostro database
   */
  private normalizeCharacter(character: AniListCharacter): NormalizedAniListCharacter {
    // Determina la serie principale (primo media associato)
    const primaryMedia = character.media?.edges?.[0]?.node;
    const mediaTitle = primaryMedia?.title?.english || 
                      primaryMedia?.title?.romaji || 
                      primaryMedia?.title?.native || 
                      'Unknown';

    // Determina la categoria
    let category: 'ANIME' | 'MANGA' | 'OTHER' = 'OTHER';
    if (primaryMedia?.type === 'ANIME') {
      category = 'ANIME';
    } else if (primaryMedia?.type === 'MANGA') {
      category = 'MANGA';
    }

    // Calcola popularity score (combinando favorites del personaggio e popolarità del media)
    const baseScore = character.favourites || 0;
    const mediaPopularityBonus = (primaryMedia?.popularity || 0) * 0.01;
    const popularityScore = baseScore + mediaPopularityBonus;

    // Estrai tags dai nomi alternativi e media
    const tags = [
      ...(character.name.alternative || []),
      mediaTitle,
      category.toLowerCase(),
      character.gender || 'Unknown Gender',
    ].filter(Boolean).slice(0, 10);

    // Raccogli tutte le apparizioni
    const animeAppearances: string[] = [];
    const mangaAppearances: string[] = [];

    character.media?.edges?.forEach(edge => {
      const title = edge.node.title.english || edge.node.title.romaji;
      if (edge.node.type === 'ANIME') {
        animeAppearances.push(title);
      } else if (edge.node.type === 'MANGA') {
        mangaAppearances.push(title);
      }
    });

    return {
      id: `anilist-${character.id}`,
      name: character.name.full,
      imageUrl: character.image.large || character.image.medium,
      favorites: character.favourites || 0,
      popularity: character.favourites || 0,
      series: mediaTitle,
      media_title: mediaTitle,
      category,
      description: character.description?.replace(/<[^>]*>/g, '').substring(0, 500), // Rimuovi HTML e limita
      tags,
      fandom: category === 'ANIME' ? 'Anime' : category === 'MANGA' ? 'Manga' : 'Other',
      gender: character.gender || 'Unknown',
      popularityScore,
      sourceUrl: character.siteUrl,
      anilistId: character.id,
      source: 'anilist',
      appearances: {
        anime: animeAppearances,
        manga: mangaAppearances,
      },
    };
  }

  /**
   * Pulisce la cache
   */
  clearCache(): void {
    cache.clear();
    console.log('AniList service cache cleared');
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
export const anilistService = new AniListService();
export default anilistService;

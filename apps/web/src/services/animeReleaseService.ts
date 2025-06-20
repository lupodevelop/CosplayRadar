/**
 * Anime Release Tracker Service
 * Analizza le uscite imminenti di anime/manga per anticipare i trend
 */

import { prisma } from '@cosplayradar/db';

// Tipi per AniList API
interface AniListMedia {
  id: number;
  title: {
    romaji: string;
    english?: string;
    native?: string;
  };
  startDate: {
    year?: number;
    month?: number;
    day?: number;
  };
  endDate?: {
    year?: number;
    month?: number;
    day?: number;
  };
  season?: 'SPRING' | 'SUMMER' | 'FALL' | 'WINTER';
  seasonYear?: number;
  status: 'NOT_YET_RELEASED' | 'RELEASING' | 'FINISHED' | 'CANCELLED' | 'HIATUS';
  format: 'TV' | 'TV_SHORT' | 'MOVIE' | 'SPECIAL' | 'OVA' | 'ONA' | 'MUSIC';
  episodes?: number;
  duration?: number;
  source?: 'ORIGINAL' | 'MANGA' | 'LIGHT_NOVEL' | 'VISUAL_NOVEL' | 'VIDEO_GAME' | 'OTHER';
  genres: string[];
  tags: Array<{ name: string }>;
  popularity: number;
  meanScore?: number;
  favourites: number;
  coverImage: {
    large?: string;
    medium?: string;
  };
  bannerImage?: string;
  description?: string;
  siteUrl: string;
  trending?: number;
  characters?: {
    nodes: Array<{
      id: number;
      name: {
        full: string;
        native?: string;
      };
      gender?: string;
      image: {
        large?: string;
        medium?: string;
      };
      description?: string;
      siteUrl: string;
      favourites: number;
    }>;
  };
}

interface AniListResponse {
  data: {
    Page: {
      pageInfo: {
        hasNextPage: boolean;
        currentPage: number;
      };
      media: AniListMedia[];
    };
  };
}

class AnimeReleaseService {
  private readonly anilistEndpoint = 'https://graphql.anilist.co';

  /**
   * Ottiene anime/manga in uscita o appena iniziati
   */
  async fetchUpcomingReleases(): Promise<{
    success: boolean;
    newReleases: number;
    updatedReleases: number;
    errors: string[];
  }> {
    console.log('🔍 Fetching upcoming anime releases from AniList...');
    
    const results = {
      success: false,
      newReleases: 0,
      updatedReleases: 0,
      errors: [] as string[]
    };

    try {
      // Query per anime in uscita nelle prossime 8 settimane
      const upcomingAnime = await this.queryUpcomingAnime();
      if (upcomingAnime.length > 0) {
        const upcomingResult = await this.saveAnimeReleases(upcomingAnime, true);
        results.newReleases += upcomingResult.newReleases;
        results.updatedReleases += upcomingResult.updatedReleases;
        results.errors.push(...upcomingResult.errors);
      }

      // Query per anime attualmente in corso (per trend analysis)
      const currentAnime = await this.queryCurrentAnime();
      if (currentAnime.length > 0) {
        const currentResult = await this.saveAnimeReleases(currentAnime, false);
        results.newReleases += currentResult.newReleases;
        results.updatedReleases += currentResult.updatedReleases;
        results.errors.push(...currentResult.errors);
      }

      // Query per anime trending
      const trendingAnime = await this.queryTrendingAnime();
      if (trendingAnime.length > 0) {
        const trendingResult = await this.saveAnimeReleases(trendingAnime, false);
        results.newReleases += trendingResult.newReleases;
        results.updatedReleases += trendingResult.updatedReleases;
        results.errors.push(...trendingResult.errors);
      }

      results.success = results.errors.length < (results.newReleases + results.updatedReleases) / 2;

      console.log(`✅ Processed ${results.newReleases} new and ${results.updatedReleases} updated releases`);
      
      return results;

    } catch (error) {
      console.error('❌ Error fetching upcoming releases:', error);
      results.errors.push(`Failed to fetch releases: ${error}`);
      return results;
    }
  }

  /**
   * Query AniList per anime in uscita
   */
  private async queryUpcomingAnime(): Promise<AniListMedia[]> {
    const currentDate = new Date();
    const futureDate = new Date();
    futureDate.setDate(currentDate.getDate() + 56); // 8 settimane

    const query = `
      query ($page: Int, $startDateGreater: FuzzyDateInt, $startDateLesser: FuzzyDateInt) {
        Page(page: $page, perPage: 50) {
          pageInfo {
            hasNextPage
            currentPage
          }
          media(
            type: ANIME, 
            status_in: [NOT_YET_RELEASED, RELEASING],
            startDate_greater: $startDateGreater,
            startDate_lesser: $startDateLesser,
            sort: [START_DATE, POPULARITY_DESC]
          ) {
            id
            title {
              romaji
              english
              native
            }
            startDate {
              year
              month
              day
            }
            endDate {
              year
              month
              day
            }
            season
            seasonYear
            status
            format
            episodes
            duration
            source
            genres
            tags {
              name
            }
            popularity
            meanScore
            favourites
            coverImage {
              large
              medium
            }
            bannerImage
            description
            siteUrl
            trending
            characters(role: MAIN, page: 1, perPage: 10) {
              nodes {
                id
                name {
                  full
                  native
                }
                gender
                image {
                  large
                  medium
                }
                description
                siteUrl
                favourites
              }
            }
          }
        }
      }
    `;

    const variables = {
      page: 1,
      startDateGreater: this.formatAniListDate(currentDate),
      startDateLesser: this.formatAniListDate(futureDate)
    };

    return await this.executeAniListQuery(query, variables);
  }

  /**
   * Query AniList per anime attualmente in corso
   */
  private async queryCurrentAnime(): Promise<AniListMedia[]> {
    const query = `
      query ($page: Int) {
        Page(page: $page, perPage: 50) {
          pageInfo {
            hasNextPage
            currentPage
          }
          media(
            type: ANIME, 
            status: RELEASING,
            sort: [POPULARITY_DESC, TRENDING_DESC]
          ) {
            id
            title {
              romaji
              english
              native
            }
            startDate {
              year
              month
              day
            }
            season
            seasonYear
            status
            format
            episodes
            duration
            source
            genres
            tags {
              name
            }
            popularity
            meanScore
            favourites
            coverImage {
              large
              medium
            }
            bannerImage
            description
            siteUrl
            trending
            characters(role: MAIN, page: 1, perPage: 10) {
              nodes {
                id
                name {
                  full
                  native
                }
                gender
                image {
                  large
                  medium
                }
                description
                siteUrl
                favourites
              }
            }
          }
        }
      }
    `;

    return await this.executeAniListQuery(query, { page: 1 });
  }

  /**
   * Query AniList per anime trending
   */
  private async queryTrendingAnime(): Promise<AniListMedia[]> {
    const query = `
      query ($page: Int) {
        Page(page: $page, perPage: 30) {
          pageInfo {
            hasNextPage
            currentPage
          }
          media(
            type: ANIME,
            sort: [TRENDING_DESC, POPULARITY_DESC]
          ) {
            id
            title {
              romaji
              english
              native
            }
            startDate {
              year
              month
              day
            }
            season
            seasonYear
            status
            format
            episodes
            duration
            source
            genres
            tags {
              name
            }
            popularity
            meanScore
            favourites
            coverImage {
              large
              medium
            }
            bannerImage
            description
            siteUrl
            trending
            characters(role: MAIN, page: 1, perPage: 10) {
              nodes {
                id
                name {
                  full
                  native
                }
                gender
                image {
                  large
                  medium
                }
                description
                siteUrl
                favourites
              }
            }
          }
        }
      }
    `;

    return await this.executeAniListQuery(query, { page: 1 });
  }

  /**
   * Esegue una query GraphQL su AniList
   */
  private async executeAniListQuery(query: string, variables: any): Promise<AniListMedia[]> {
    try {
      const response = await fetch(this.anilistEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ query, variables })
      });

      if (!response.ok) {
        throw new Error(`AniList API error: ${response.status}`);
      }

      const data: AniListResponse = await response.json();
      
      if (!data.data?.Page?.media) {
        console.warn('⚠️  No media data in AniList response');
        return [];
      }

      return data.data.Page.media;

    } catch (error) {
      console.error('❌ AniList query failed:', error);
      throw error;
    }
  }

  /**
   * Salva le release nel database
   */
  private async saveAnimeReleases(animeList: AniListMedia[], isUpcoming: boolean): Promise<{
    newReleases: number;
    updatedReleases: number;
    errors: string[];
  }> {
    const result = {
      newReleases: 0,
      updatedReleases: 0,
      errors: [] as string[]
    };

    for (const anime of animeList) {
      try {
        const startDate = this.parseAniListDate(anime.startDate);
        const endDate = anime.endDate ? this.parseAniListDate(anime.endDate) : null;
        
        // Determina se è nuovo (< 1 mese dall'inizio)
        const isNew = startDate ? 
          (Date.now() - startDate.getTime()) < (30 * 24 * 60 * 60 * 1000) : false;

        // Determina se è imminente (< 2 settimane)
        const isUpcomingRelease = startDate ? 
          (startDate.getTime() - Date.now()) < (14 * 24 * 60 * 60 * 1000) && 
          startDate.getTime() > Date.now() : false;

        const animeData = {
          anilistId: anime.id,
          title: anime.title.romaji,
          englishTitle: anime.title.english || null,
          nativeTitle: anime.title.native || null,
          status: anime.status as any,
          format: anime.format as any,
          startDate,
          endDate,
          season: anime.season as any,
          seasonYear: anime.seasonYear || null,
          episodes: anime.episodes || null,
          duration: anime.duration || null,
          source: anime.source as any,
          genres: anime.genres,
          tags: anime.tags.map(tag => tag.name),
          popularity: anime.popularity,
          meanScore: anime.meanScore || null,
          favourites: anime.favourites,
          coverImage: anime.coverImage.large || anime.coverImage.medium || null,
          bannerImage: anime.bannerImage || null,
          description: anime.description || null,
          siteUrl: anime.siteUrl,
          isNew,
          isUpcoming: isUpcomingRelease,
          isTrending: !!anime.trending && anime.trending > 0,
          trendRank: anime.trending || null,
          lastChecked: new Date()
        };

        // Upsert anime release
        const existingAnime = await prisma.animeRelease.findUnique({
          where: { anilistId: anime.id }
        });

        if (existingAnime) {
          await prisma.animeRelease.update({
            where: { anilistId: anime.id },
            data: animeData
          });
          result.updatedReleases++;
        } else {
          await prisma.animeRelease.create({
            data: animeData
          });
          result.newReleases++;
        }

        // Salva i personaggi associati
        if (anime.characters?.nodes) {
          await this.saveAnimeCharacters(anime.id, anime.characters.nodes);
        }

        console.log(`📝 Processed: ${anime.title.romaji} (${isNew ? 'NEW' : 'UPDATE'})`);

      } catch (error) {
        console.error(`❌ Error processing anime ${anime.title.romaji}:`, error);
        result.errors.push(`Failed to process ${anime.title.romaji}: ${error}`);
      }
    }

    return result;
  }

  /**
   * Salva i personaggi associati all'anime
   */
  private async saveAnimeCharacters(animeId: number, characters: any[]): Promise<void> {
    for (const character of characters) {
      try {
        // Controlla se il personaggio esiste già
        const existingCharacter = await prisma.character.findFirst({
          where: {
            OR: [
              { anilistId: character.id },
              { name: character.name.full }
            ]
          }
        });

        const characterData = {
          name: character.name.full,
          series: 'Unknown', // Sarà aggiornato dal sync
          category: 'ANIME' as any,
          difficulty: 3, // Default
          popularity: character.favourites || 0,
          imageUrl: character.image?.large || character.image?.medium || null,
          description: character.description || null,
          gender: character.gender || 'Unknown',
          popularityScore: character.favourites || 0,
          sourceUrl: character.siteUrl,
          anilistId: character.id,
          source: 'anilist'
        };

        if (existingCharacter) {
          // Aggiorna solo se ci sono nuovi dati
          await prisma.character.update({
            where: { id: existingCharacter.id },
            data: {
              ...characterData,
              popularity: Math.max(existingCharacter.popularity, characterData.popularity),
              popularityScore: Math.max(existingCharacter.popularityScore, characterData.popularityScore)
            }
          });
        } else {
          // Crea nuovo personaggio
          await prisma.character.create({
            data: characterData
          });
        }

      } catch (error) {
        console.error(`❌ Error saving character ${character.name.full}:`, error);
      }
    }
  }

  /**
   * Converte data AniList in Date
   */
  private parseAniListDate(anilistDate: { year?: number; month?: number; day?: number }): Date | null {
    if (!anilistDate.year) return null;
    
    return new Date(
      anilistDate.year,
      (anilistDate.month || 1) - 1, // JavaScript months are 0-indexed
      anilistDate.day || 1
    );
  }

  /**
   * Formatta Date per AniList query
   */
  private formatAniListDate(date: Date): number {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return parseInt(`${year}${month}${day}`);
  }

  /**
   * Ottiene statistiche sulle release
   */
  async getReleaseStats(): Promise<{
    totalReleases: number;
    upcomingReleases: number;
    newReleases: number;
    trendingReleases: number;
    recentlyUpdated: number;
  }> {
    try {
      const [total, upcoming, newReleases, trending, recent] = await Promise.all([
        prisma.animeRelease.count(),
        prisma.animeRelease.count({ where: { isUpcoming: true } }),
        prisma.animeRelease.count({ where: { isNew: true } }),
        prisma.animeRelease.count({ where: { isTrending: true } }),
        prisma.animeRelease.count({
          where: {
            lastChecked: {
              gte: new Date(Date.now() - 24 * 60 * 60 * 1000) // Ultimi 24 ore
            }
          }
        })
      ]);

      return {
        totalReleases: total,
        upcomingReleases: upcoming,
        newReleases,
        trendingReleases: trending,
        recentlyUpdated: recent
      };

    } catch (error) {
      console.error('❌ Error getting release stats:', error);
      return {
        totalReleases: 0,
        upcomingReleases: 0,
        newReleases: 0,
        trendingReleases: 0,
        recentlyUpdated: 0
      };
    }
  }
}

// Export singleton
export const animeReleaseService = new AnimeReleaseService();
export default animeReleaseService;

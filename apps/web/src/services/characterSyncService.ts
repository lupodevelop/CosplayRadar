/**
 * Character Sync Service
 * Sincronizza i personaggi dall'API Jikan al database locale
 */

import { prisma } from '@cosplayradar/db';
import { jikanService, type NormalizedCharacter } from './jikanService';
import { anilistService, type NormalizedAniListCharacter } from './anilistService';
import cron from 'node-cron';

export class CharacterSyncService {
  private isRunning = false;

  /**
   * Sincronizza i personaggi trending dal database Jikan
   */
  async syncDailyCharacters(): Promise<{
    success: boolean;
    syncedCount: number;
    updatedCount: number;
    errors: string[];
  }> {
    if (this.isRunning) {
      throw new Error('Sync is already running');
    }

    this.isRunning = true;
    console.log('Starting daily character sync with trending data...');

    const errors: string[] = [];
    let syncedCount = 0;
    let updatedCount = 0;

    try {
      // Ottieni personaggi trending e della stagione corrente (più pagine)
      console.log('Syncing trending characters from Jikan...');
      
      // Sincronizza le prime 3 pagine per avere ~75 personaggi
      for (let page = 1; page <= 3; page++) {
        const result = await jikanService.getTopCharacters({ page });
        
        for (const character of result.characters) {
          try {
            const existingCount = await this.syncCharacter(character);
            if (existingCount) {
              updatedCount++;
            } else {
              syncedCount++;
            }
          } catch (error) {
            console.error(`Error syncing character ${character.name}:`, error);
            errors.push(`Failed to sync ${character.name}: ${error}`);
          }
        }
        
        // Delay tra le pagine per rispettare i rate limits
        await new Promise(resolve => setTimeout(resolve, 2000)); // Jikan ha rate limits più stretti
      }

      // Aggiorna le tendenze
      await this.updateTrendData();
      
      console.log(`Sync completed. Synced: ${syncedCount}, Updated: ${updatedCount}, Errors: ${errors.length}`);
      
      return {
        success: errors.length === 0,
        syncedCount,
        updatedCount,
        errors,
      };
    } catch (error) {
      console.error('Fatal error during sync:', error);
      errors.push(`Fatal error: ${error}`);
      
      return {
        success: false,
        syncedCount,
        updatedCount,
        errors,
      };
    } finally {
      this.isRunning = false;
    }
  }

  /**
   * Sincronizza un singolo personaggio
   */
  private async syncCharacter(character: NormalizedCharacter): Promise<boolean> {
    // Controlla se il personaggio esiste già
    const existing = await prisma.character.findFirst({
      where: {
        OR: [
          { id: character.id },
          { name: character.name, series: character.series },
        ],
      },
    });

    const characterData = {
      name: character.name,
      series: character.series,
      category: character.category as any,
      difficulty: Math.ceil(character.popularity / 10000) || 1,
      popularity: character.popularity,
      imageUrl: character.imageUrl,
      description: character.description,
      tags: character.tags,
      fandom: character.fandom,
      gender: character.gender,
      popularityScore: character.popularityScore,
      sourceUrl: character.sourceUrl,
    };

    if (existing) {
      // Aggiorna il personaggio esistente
      await prisma.character.update({
        where: { id: existing.id },
        data: {
          ...characterData,
          updatedAt: new Date(),
        },
      });
      
      console.log(`Updated character: ${character.name}`);
      return true;
    } else {
      // Crea nuovo personaggio
      await prisma.character.create({
        data: {
          ...characterData,
          id: character.id,
        },
      });
      
      console.log(`Created character: ${character.name}`);
      return false;
    }
  }

  /**
   * Sincronizza personaggi da AniList (weekly trending con generi)
   */
  async syncAniListCharacters(): Promise<{
    success: boolean;
    syncedCount: number;
    updatedCount: number;
    errors: string[];
  }> {
    if (this.isRunning) {
      throw new Error('Sync is already running');
    }

    this.isRunning = true;
    console.log('Starting AniList character sync with top characters...');

    const errors: string[] = [];
    let syncedCount = 0;
    let updatedCount = 0;

    try {
      // Prima sincronizza i personaggi più popolari in generale (più pagine)
      console.log('Syncing AniList top characters...');
      
      // Sincronizza le prime 3 pagine per avere ~75 personaggi
      for (let page = 1; page <= 3; page++) {
        const topResult = await anilistService.getTopCharacters({ page, perPage: 25 });
        
        for (const character of topResult.characters) {
          try {
            const existingCount = await this.syncAniListCharacter(character);
            if (existingCount) {
              updatedCount++;
            } else {
              syncedCount++;
            }
          } catch (error) {
            console.error(`Error syncing AniList character ${character.name}:`, error);
            errors.push(`Failed to sync ${character.name}: ${error}`);
          }
        }
        
        // Delay tra le pagine per rispettare i rate limits
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      // Aggiungi anche alcuni personaggi per genere specifico
      const genders = ['Male', 'Female'] as const;
      for (const gender of genders) {
        try {
          const genderResult = await anilistService.getTopCharacters({ 
            gender, 
            page: 1, 
            perPage: 10 
          });
          
          for (const character of genderResult.characters.slice(0, 5)) { // Solo i top 5 per genere
            try {
              const existingCount = await this.syncAniListCharacter(character);
              if (existingCount) {
                updatedCount++;
              } else {
                syncedCount++;
              }
            } catch (error) {
              console.error(`Error syncing ${gender} character ${character.name}:`, error);
              errors.push(`Failed to sync ${gender} character ${character.name}: ${error}`);
            }
          }
        } catch (error) {
          console.error(`Error fetching ${gender} characters:`, error);
          errors.push(`Failed to fetch ${gender} characters: ${error}`);
        }
      }

      // Aggiorna le tendenze
      await this.updateTrendData();
      
      console.log(`AniList sync completed. Synced: ${syncedCount}, Updated: ${updatedCount}, Errors: ${errors.length}`);
      
      return {
        success: errors.length === 0,
        syncedCount,
        updatedCount,
        errors,
      };
    } catch (error) {
      console.error('Fatal error during AniList sync:', error);
      errors.push(`Fatal error: ${error}`);
      
      return {
        success: false,
        syncedCount,
        updatedCount,
        errors,
      };
    } finally {
      this.isRunning = false;
    }
  }

  /**
   * Sincronizza un singolo personaggio AniList
   */
  private async syncAniListCharacter(character: NormalizedAniListCharacter): Promise<boolean> {
    // Controlla se il personaggio esiste già
    const existing = await prisma.character.findFirst({
      where: {
        OR: [
          { id: character.id },
          { name: character.name, series: character.series },
        ],
      },
    });

    const characterData = {
      name: character.name,
      series: character.series,
      category: character.category as any,
      difficulty: Math.min(Math.ceil(character.popularity / 5000), 5), // Calcola difficoltà dalla popolarità
      popularity: character.popularity,
      imageUrl: character.imageUrl,
      description: character.description,
      tags: character.tags,
      fandom: character.fandom,
      gender: character.gender,
      popularityScore: character.popularityScore,
      sourceUrl: character.sourceUrl,
      // Campi specifici AniList
      source: character.source,
      media_title: character.media_title,
      anilistId: character.anilistId,
    };

    if (existing) {
      // Aggiorna il personaggio esistente
      await prisma.character.update({
        where: { id: existing.id },
        data: {
          ...characterData,
          updatedAt: new Date(),
        },
      });
      
      console.log(`Updated AniList character: ${character.name} (${character.gender})`);
      return true;
    } else {
      // Crea nuovo personaggio
      await prisma.character.create({
        data: {
          ...characterData,
          id: character.id,
        },
      });
      
      console.log(`Created AniList character: ${character.name} (${character.gender})`);
      return false;
    }
  }

  /**
   * Aggiorna i dati di tendenza per tutti i personaggi
   */
  private async updateTrendData(): Promise<void> {
    console.log('Updating trend data...');
    
    const characters = await prisma.character.findMany({
      select: {
        id: true,
        name: true,
        popularity: true,
        popularityScore: true,
      },
    });

    for (const character of characters) {
      try {
        // Calcola engagement basato sulla popolarità
        const engagement = Math.min(character.popularityScore / 100, 100);
        
        // Genera sentiment casuale ma realistico (di solito positivo per personaggi popolari)
        const sentiment = Math.random() * 0.4 + 0.6; // 0.6 - 1.0
        
        await prisma.trendData.create({
          data: {
            characterId: character.id,
            platform: 'REDDIT',
            mentions: Math.floor(character.popularityScore / 10),
            engagement,
            sentiment,
            date: new Date(),
          },
        });
      } catch (error) {
        console.error(`Error updating trend data for ${character.name}:`, error);
      }
    }
    
    console.log(`Updated trend data for ${characters.length} characters`);
  }

  /**
   * Avvia il scheduler automatico
   */
  startScheduler(): void {
    // Esegui ogni giorno alle 06:00
    cron.schedule('0 6 * * *', async () => {
      console.log('Starting scheduled character sync...');
      try {
        await this.syncDailyCharacters();
      } catch (error) {
        console.error('Scheduled sync failed:', error);
      }
    });

    console.log('Character sync scheduler started (daily at 06:00)');
  }

  /**
   * Ferma il sync se in corso
   */
  stopSync(): void {
    if (this.isRunning) {
      this.isRunning = false;
      console.log('Sync operation cancelled');
    }
  }

  /**
   * Ottieni lo stato del sync
   */
  getSyncStatus(): { isRunning: boolean } {
    return { isRunning: this.isRunning };
  }

  /**
   * Pulisce i dati di tendenza vecchi (più di 30 giorni)
   */
  async cleanOldTrendData(): Promise<number> {
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    const result = await prisma.trendData.deleteMany({
      where: {
        date: {
          lt: thirtyDaysAgo,
        },
      },
    });

    console.log(`Cleaned ${result.count} old trend data records`);
    return result.count;
  }

  /**
   * Ottieni statistiche di sincronizzazione
   */
  async getSyncStats(): Promise<{
    totalCharacters: number;
    recentTrends: number;
    lastSyncDate?: Date;
  }> {
    const totalCharacters = await prisma.character.count();
    
    const oneDayAgo = new Date();
    oneDayAgo.setDate(oneDayAgo.getDate() - 1);
    
    const recentTrends = await prisma.trendData.count({
      where: {
        date: {
          gte: oneDayAgo,
        },
      },
    });

    const lastTrend = await prisma.trendData.findFirst({
      orderBy: {
        date: 'desc',
      },
      select: {
        date: true,
      },
    });

    return {
      totalCharacters,
      recentTrends,
      lastSyncDate: lastTrend?.date,
    };
  }

  /**
   * Migliora i personaggi Jikan con dati da AniList (genere, serie, ecc.)
   */
  async enhanceJikanCharactersWithAniList(): Promise<{
    success: boolean;
    enhancedCount: number;
    errors: string[];
  }> {
    console.log('Starting enhancement of Jikan characters with AniList data...');
    
    const errors: string[] = [];
    let enhancedCount = 0;

    try {
      // Trova tutti i personaggi Jikan senza genere o con serie "Unknown"
      const jikanCharacters = await prisma.character.findMany({
        where: {
          source: 'jikan',
          OR: [
            { gender: 'Unknown' },
            { gender: null },
            { series: 'Unknown' },
            { anilistId: null }
          ]
        }
      });

      console.log(`Found ${jikanCharacters.length} Jikan characters to enhance`);

      for (const jikanChar of jikanCharacters) {
        try {
          // Cerca il personaggio su AniList per nome
          const searchResult = await anilistService.searchCharacters(
            jikanChar.name,
            1,
            5
          );

          if (searchResult.characters.length > 0) {
            // Trova il miglior match (stesso nome o molto simile)
            const bestMatch = searchResult.characters.find(c => 
              c.name.toLowerCase() === jikanChar.name.toLowerCase() ||
              c.name.toLowerCase().includes(jikanChar.name.toLowerCase()) ||
              jikanChar.name.toLowerCase().includes(c.name.toLowerCase())
            ) || searchResult.characters[0];

            // Aggiorna il personaggio Jikan con i dati AniList
            const enhancedData: any = {};
            
            if (bestMatch.gender && bestMatch.gender !== 'Unknown' && 
                (!jikanChar.gender || jikanChar.gender === 'Unknown')) {
              enhancedData.gender = bestMatch.gender;
            }
            
            if (bestMatch.series && bestMatch.series !== 'Unknown' && 
                (!jikanChar.series || jikanChar.series === 'Unknown')) {
              enhancedData.series = bestMatch.series;
            }
            
            if (bestMatch.media_title && !jikanChar.media_title) {
              enhancedData.media_title = bestMatch.media_title;
            }
            
            if (bestMatch.anilistId && !jikanChar.anilistId) {
              enhancedData.anilistId = bestMatch.anilistId;
            }

            // Se abbiamo dati da aggiornare
            if (Object.keys(enhancedData).length > 0) {
              await prisma.character.update({
                where: { id: jikanChar.id },
                data: {
                  ...enhancedData,
                  updatedAt: new Date()
                }
              });

              enhancedCount++;
              console.log(`Enhanced ${jikanChar.name} with AniList data: ${JSON.stringify(enhancedData)}`);
            }
          }

          // Rate limiting per AniList
          await new Promise(resolve => setTimeout(resolve, 1000));
          
        } catch (error) {
          console.error(`Error enhancing ${jikanChar.name}:`, error);
          errors.push(`Failed to enhance ${jikanChar.name}: ${error}`);
        }
      }

      return {
        success: errors.length === 0,
        enhancedCount,
        errors
      };

    } catch (error) {
      console.error('Fatal error during enhancement:', error);
      errors.push(`Fatal error: ${error}`);
      
      return {
        success: false,
        enhancedCount,
        errors
      };
    }
  }
}

// Export singleton instance
export const characterSyncService = new CharacterSyncService();
export default characterSyncService;

/**
 * Test unitari per JikanService
 */

import { jest } from '@jest/globals';
import axios from 'axios';
import { jikanService } from '@/services/jikanService';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock data
const mockJikanCharacter = {
  mal_id: 40,
  url: 'https://myanimelist.net/character/40/Spike_Spiegel',
  images: {
    jpg: {
      image_url: 'https://cdn.myanimelist.net/images/characters/4/50197.jpg',
    },
    webp: {
      image_url: 'https://cdn.myanimelist.net/images/characters/4/50197.webp',
    },
  },
  name: 'Spike Spiegel',
  name_kanji: 'スパイク・スピーゲル',
  nicknames: ['Space Cowboy'],
  favorites: 15234,
  about: 'Spike Spiegel is a tall and lean 27-year-old bounty hunter...',
  anime: [
    {
      role: 'Main',
      anime: {
        mal_id: 1,
        url: 'https://myanimelist.net/anime/1/Cowboy_Bebop',
        images: {
          jpg: {
            image_url: 'https://cdn.myanimelist.net/images/anime/4/19644.jpg',
          },
        },
        title: 'Cowboy Bebop',
      },
    },
  ],
  manga: [],
  voices: [],
};

const mockJikanResponse = {
  data: [mockJikanCharacter],
  pagination: {
    last_visible_page: 100,
    has_next_page: true,
    current_page: 1,
    items: {
      count: 25,
      total: 2500,
      per_page: 25,
    },
  },
};

describe('JikanService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jikanService.clearCache(); // Pulisce cache tra i test
  });

  describe('getTopCharacters', () => {
    it('dovrebbe ottenere e normalizzare i personaggi top', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        data: mockJikanResponse,
      });

      const result = await jikanService.getTopCharacters({ page: 1 });

      expect(mockedAxios.get).toHaveBeenCalledWith(
        'https://api.jikan.moe/v4/top/characters',
        {
          params: { page: 1 },
          timeout: 10000,
        }
      );

      expect(result).toMatchObject({
        characters: expect.any(Array),
        pagination: {
          currentPage: 1,
          hasNextPage: true,
          totalPages: 100,
        },
      });

      expect(result.characters).toHaveLength(1);
      
      const character = result.characters[0];
      expect(character).toMatchObject({
        id: '40',
        name: 'Spike Spiegel',
        imageUrl: 'https://cdn.myanimelist.net/images/characters/4/50197.jpg',
        favorites: 15234,
        series: 'Cowboy Bebop',
        category: 'ANIME',
        fandom: 'Anime',
        malId: 40,
        sourceUrl: 'https://myanimelist.net/character/40/Spike_Spiegel',
      });
    });

    it('dovrebbe usare la cache per richieste duplicate', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        data: mockJikanResponse,
      });

      // Prima chiamata
      await jikanService.getTopCharacters({ page: 1 });
      
      // Seconda chiamata (dovrebbe usare cache)
      await jikanService.getTopCharacters({ page: 1 });

      // Axios dovrebbe essere chiamato solo una volta
      expect(mockedAxios.get).toHaveBeenCalledTimes(1);
    });

    it('dovrebbe gestire errori di rate limiting', async () => {
      mockedAxios.get.mockRejectedValueOnce({
        isAxiosError: true,
        response: { status: 429 },
      });

      await expect(jikanService.getTopCharacters()).rejects.toThrow(
        'Rate limit exceeded. Please try again later.'
      );
    });

    it('dovrebbe gestire errori del server', async () => {
      mockedAxios.get.mockRejectedValueOnce({
        isAxiosError: true,
        response: { status: 500 },
      });

      await expect(jikanService.getTopCharacters()).rejects.toThrow(
        'Jikan API server error. Please try again later.'
      );
    });

    it('dovrebbe gestire risposte invalide', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        data: null,
      });

      await expect(jikanService.getTopCharacters()).rejects.toThrow(
        'Invalid response from Jikan API'
      );
    });
  });

  describe('getCharacterById', () => {
    it('dovrebbe ottenere un personaggio specifico', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        data: { data: mockJikanCharacter },
      });

      const result = await jikanService.getCharacterById(40);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        'https://api.jikan.moe/v4/characters/40'
      );

      expect(result).toMatchObject({
        id: '40',
        name: 'Spike Spiegel',
        malId: 40,
      });
    });

    it('dovrebbe restituire null per personaggio non trovato', async () => {
      mockedAxios.get.mockRejectedValueOnce({
        isAxiosError: true,
        response: { status: 404 },
      });

      const result = await jikanService.getCharacterById(999999);

      expect(result).toBeNull();
    });
  });

  describe('searchCharacters', () => {
    it('dovrebbe cercare personaggi per nome', async () => {
      mockedAxios.get.mockResolvedValueOnce({
        data: mockJikanResponse,
      });

      const result = await jikanService.searchCharacters('Spike', 1);

      expect(mockedAxios.get).toHaveBeenCalledWith(
        'https://api.jikan.moe/v4/characters',
        {
          params: {
            q: 'Spike',
            page: 1,
            limit: 25,
          },
        }
      );

      expect(result.characters).toHaveLength(1);
      expect(result.characters[0].name).toBe('Spike Spiegel');
    });
  });

  describe('normalizeCharacter', () => {
    it('dovrebbe normalizzare correttamente un personaggio anime', () => {
      // Accesso al metodo privato per test
      const normalizeCharacter = (jikanService as any).normalizeCharacter.bind(jikanService);
      
      const normalized = normalizeCharacter(mockJikanCharacter);

      expect(normalized).toMatchObject({
        id: '40',
        name: 'Spike Spiegel',
        series: 'Cowboy Bebop',
        category: 'ANIME',
        fandom: 'Anime',
        popularityScore: 152.34,
        tags: expect.arrayContaining(['Space Cowboy', 'Cowboy Bebop']),
        appearances: {
          anime: ['Cowboy Bebop'],
          manga: [],
        },
      });
    });

    it('dovrebbe determinare la categoria manga correttamente', () => {
      const mangaCharacter = {
        ...mockJikanCharacter,
        anime: [],
        manga: [
          {
            role: 'Main',
            manga: {
              mal_id: 1,
              url: 'https://myanimelist.net/manga/1/Monster',
              images: { jpg: { image_url: 'test.jpg' } },
              title: 'Monster',
            },
          },
        ],
      };

      const normalizeCharacter = (jikanService as any).normalizeCharacter.bind(jikanService);
      const normalized = normalizeCharacter(mangaCharacter);

      expect(normalized.category).toBe('MANGA');
      expect(normalized.fandom).toBe('Manga');
      expect(normalized.series).toBe('Monster');
    });
  });

  describe('extractGender', () => {
    it('dovrebbe estrarre il genere maschile', () => {
      const extractGender = (jikanService as any).extractGender.bind(jikanService);
      
      const maleText = 'He is a bounty hunter who travels with his crew.';
      expect(extractGender(maleText)).toBe('Male');
    });

    it('dovrebbe estrarre il genere femminile', () => {
      const extractGender = (jikanService as any).extractGender.bind(jikanService);
      
      const femaleText = 'She is a skilled fighter who protects her friends.';
      expect(extractGender(femaleText)).toBe('Female');
    });

    it('dovrebbe restituire Unknown per genere indeterminato', () => {
      const extractGender = (jikanService as any).extractGender.bind(jikanService);
      
      const unknownText = 'This character is mysterious and powerful.';
      expect(extractGender(unknownText)).toBe('Unknown');
    });
  });

  describe('cache management', () => {
    it('dovrebbe fornire statistiche della cache', () => {
      const stats = jikanService.getCacheStats();
      
      expect(stats).toHaveProperty('size');
      expect(stats).toHaveProperty('max');
      expect(stats).toHaveProperty('calculatedSize');
    });

    it('dovrebbe pulire la cache', () => {
      jikanService.clearCache();
      const stats = jikanService.getCacheStats();
      
      expect(stats.size).toBe(0);
    });
  });
});

// Test di integrazione (opzionali, richiedono connessione internet)
describe('JikanService Integration Tests', () => {
  // Questi test sono skippati di default per evitare dipendenze da API esterne
  describe.skip('Real API calls', () => {
    it('dovrebbe ottenere personaggi reali dall\'API', async () => {
      const result = await jikanService.getTopCharacters({ page: 1 });
      
      expect(result.characters.length).toBeGreaterThan(0);
      expect(result.characters[0]).toHaveProperty('name');
      expect(result.characters[0]).toHaveProperty('imageUrl');
      expect(result.characters[0]).toHaveProperty('malId');
    }, 10000); // Timeout più lungo per API reali
  });
});

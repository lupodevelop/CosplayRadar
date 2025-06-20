'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Character {
  id: number;
  name: string;
  nameNative?: string;
  image?: string;
  description?: string;
  gender: string;
  favourites: number;
  favouritesFormatted?: string;
  siteUrl?: string;
  cosplayScore: number;
  cosplayDifficulty: number;
  hasGoogleTrends?: boolean;
  trendDirection?: 'up' | 'down' | null;
  trendPercentage?: number | null;
  isTrending?: boolean;
}

interface AnimeRelease {
  id: string;
  anilistId?: number;
  title: string;
  titleEnglish?: string;
  popularity: number;
  season: string;
  seasonYear: number;
  status: string;
  format: string;
  episodes?: number;
  meanScore?: number;
  favourites: number;
  startDate?: string;
  coverImageLarge?: string;
  coverImageMedium?: string;
  description?: string;
  genres: string[];
  trending: number;
  characters?: Character[];
}

interface AnimeReleaseStats {
  totalReleases: number;
  avgPopularity: number;
  avgScore: number;
  totalCharacters: number;
  avgCharactersPerAnime: number;
  topTrendingCharacters: Array<Character & { animeName: string }>;
  topCharactersByFavourites: Array<Character & { animeName: string }>;
}

interface SyncResult {
  success: boolean;
  message: string;
  stats: {
    syncedAnime: number;
    syncedCharacters: number;
    totalFetched: number;
    errors: number;
  };
  errors?: string[];
}

// Funzione per formattare i numeri
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
};

// Funzione per ottenere l'indicatore visuale di popolarità
const getPopularityIndicator = (favourites: number) => {
  if (favourites >= 50000) {
    return { icon: '🔥', color: 'text-red-500', bg: 'bg-red-100', level: 'VIRAL' };
  } else if (favourites >= 20000) {
    return { icon: '⚡', color: 'text-orange-500', bg: 'bg-orange-100', level: 'HOT' };
  } else if (favourites >= 10000) {
    return { icon: '🚀', color: 'text-purple-500', bg: 'bg-purple-100', level: 'TREND' };
  } else if (favourites >= 5000) {
    return { icon: '👍', color: 'text-blue-500', bg: 'bg-blue-100', level: 'GOOD' };
  } else if (favourites >= 1000) {
    return { icon: '📈', color: 'text-green-500', bg: 'bg-green-100', level: 'RISING' };
  } else {
    return { icon: '💡', color: 'text-gray-500', bg: 'bg-gray-100', level: 'NEW' };
  }
};

// Funzione per ottenere barre di popolarità
const getPopularityBars = (favourites: number, maxFavourites: number = 100000) => {
  const percentage = Math.min((favourites / maxFavourites) * 100, 100);
  const bars = Math.ceil(percentage / 20); // 5 barre max
  return bars;
};

export default function AnimeReleasesPage() {
  const [animeReleases, setAnimeReleases] = useState<AnimeRelease[]>([]);
  const [stats, setStats] = useState<AnimeReleaseStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnimeReleases();
  }, []);

  const fetchAnimeReleases = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/anime-releases');
      const data = await response.json();
      
      if (data.success) {
        setAnimeReleases(data.data || []);
        setStats(data.stats);
      } else {
        setError(data.error || 'Errore nel caricamento dei dati');
      }
    } catch (error) {
      console.error('Error fetching anime releases:', error);
      setError('Errore nella connessione al server');
    } finally {
      setLoading(false);
    }
  };

  const syncAnimeReleases = async () => {
    try {
      setSyncing(true);
      setError(null);
      setSyncResult(null);
      
      const response = await fetch('/api/admin/anime-releases?action=sync');
      const result = await response.json();
      
      setSyncResult(result);
      
      if (result.success) {
        await fetchAnimeReleases();
      } else {
        setError(`Errore durante il sync: ${result.error}`);
      }
      
    } catch (error) {
      console.error('Error syncing anime releases:', error);
      setError('Errore durante la sincronizzazione');
    } finally {
      setSyncing(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('it-IT');
    } catch {
      return 'Data non disponibile';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'RELEASING': return 'bg-green-100 text-green-800';
      case 'NOT_YET_RELEASED': return 'bg-blue-100 text-blue-800';
      case 'FINISHED': return 'bg-gray-100 text-gray-800';
      case 'CANCELLED': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeasonEmoji = (season: string) => {
    switch (season) {
      case 'SPRING': return '🌸';
      case 'SUMMER': return '☀️';
      case 'FALL': return '🍂';
      case 'WINTER': return '❄️';
      default: return '📅';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-xl text-gray-600">Caricamento anime releases...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                🎬 Anime Releases - Estate 2025
              </h1>
              <p className="text-gray-600">
                Monitora le uscite imminenti per anticipare i trend cosplay
              </p>
            </div>
            <Link
              href="/admin"
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
            >
              ← Torna alla Dashboard
            </Link>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Basic Test Content */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            🔥 Test Dashboard
          </h2>
          <p className="text-gray-600">
            Dashboard caricata correttamente! Le funzionalità complete saranno disponibili a breve.
          </p>
          
          {/* Test degli indicatori */}
          <div className="mt-6 space-y-4">
            <h3 className="text-lg font-semibold">Test Indicatori:</h3>
            {[1000, 5000, 15000, 30000, 60000].map((num) => {
              const indicator = getPopularityIndicator(num);
              return (
                <div key={num} className="flex items-center space-x-3">
                  <span className={`${indicator.color} text-2xl`}>{indicator.icon}</span>
                  <span className={`px-3 py-1 rounded-full font-bold ${indicator.color} ${indicator.bg}`}>
                    {indicator.level}
                  </span>
                  <span className="text-gray-600">{formatNumber(num)} favoriti</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

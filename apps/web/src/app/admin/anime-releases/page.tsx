'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { PopularityBadge, PopularityBars } from '@/components/popularity-indicators';
import { PopularityBadge, PopularityBars } from '@/components/popularity-indicators';

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
  cosplayScore: nu                          <PopularityBars score={character.favourites || 0} />
                        </div>
                        
                        {/* Character Description */}fficulty: number;
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

// Funzione per ottenere l'indicatore visuale di popolarità basato su percentili reali
const getPopularityIndicator = (favourites: number) => {
  // Basato sui dati reali: converti favoriti in score normalizzato
  const popularityScore = favourites / 1000; // Normalizza i favoriti
  
  if (popularityScore >= 85) { // Top 10% - Personaggi leggendari
    return { icon: '�', color: 'text-yellow-500', bg: 'bg-yellow-100', level: 'LEGENDARY' };
  } else if (popularityScore >= 40) { // Top 25% - Elite
    return { icon: '⭐', color: 'text-purple-500', bg: 'bg-purple-100', level: 'ELITE' };
  } else if (popularityScore >= 28) { // Top 50% - Popolari
    return { icon: '�', color: 'text-red-500', bg: 'bg-red-100', level: 'POPULAR' };
  } else if (popularityScore >= 17) { // Top 75% - Conosciuti
    return { icon: '👍', color: 'text-blue-500', bg: 'bg-blue-100', level: 'KNOWN' };
  } else if (popularityScore >= 5) { // Emergenti
    return { icon: '📈', color: 'text-green-500', bg: 'bg-green-100', level: 'EMERGING' };
  } else {
    return { icon: '�', color: 'text-gray-500', bg: 'bg-gray-100', level: 'FRESH' };
  }
};

// Funzione per ottenere barre di popolarità proporzionali
const getPopularityBars = (favourites: number) => {
  const popularityScore = favourites / 1000;
  
  // Sistema a 5 barre basato sui percentili
  if (popularityScore >= 85) return 5;      // LEGENDARY
  else if (popularityScore >= 40) return 4; // ELITE  
  else if (popularityScore >= 28) return 3; // POPULAR
  else if (popularityScore >= 17) return 2; // KNOWN
  else if (popularityScore >= 5) return 1;  // EMERGING
  else return 0; // FRESH
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
        // Refresh data after sync
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

        {/* Sync Result */}
        {syncResult && (
          <div className={`border px-4 py-3 rounded mb-6 ${
            syncResult.success 
              ? 'bg-green-100 border-green-400 text-green-700' 
              : 'bg-yellow-100 border-yellow-400 text-yellow-700'
          }`}>
            <h3 className="font-bold mb-2">{syncResult.message}</h3>
            <p>Anime sincronizzati: {syncResult.stats.syncedAnime}</p>
            <p>Personaggi aggiunti: {syncResult.stats.syncedCharacters}</p>
            <p>Totale recuperati: {syncResult.stats.totalFetched}</p>
            {syncResult.errors && syncResult.errors.length > 0 && (
              <p>Errori: {syncResult.stats.errors}</p>
            )}
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl mr-4">🎬</div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Anime</h3>
                <p className="text-2xl font-bold text-blue-600">{stats?.totalReleases || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl mr-4">👥</div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Characters</h3>
                <p className="text-2xl font-bold text-purple-600">{stats?.totalCharacters || 0}</p>
                <p className="text-xs text-gray-500">~{stats?.avgCharactersPerAnime || 0} per anime</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl mr-4">📈</div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Avg Popularity</h3>
                <p className="text-2xl font-bold text-green-600">{formatNumber(stats?.avgPopularity || 0)}</p>
                <p className="text-xs text-gray-500">Media molto alta</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl mr-4">⭐</div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Avg Score</h3>
                <p className="text-2xl font-bold text-yellow-600">{stats?.avgScore || 'N/A'}</p>
                <p className="text-xs text-gray-500">Punteggio medio</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <button
              onClick={syncAnimeReleases}
              disabled={syncing}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 px-4 rounded-lg transition-colors"
            >
              {syncing ? '🔄 Sincronizzazione...' : '🔄 Sync da AniList'}
            </button>
          </div>
        </div>

        {/* Top Trending Characters Section */}
        {stats?.topTrendingCharacters && stats.topTrendingCharacters.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                🔥 Personaggi in Trending
              </h2>
              <span className="bg-red-100 text-red-800 text-sm font-medium px-3 py-1 rounded-full">
                {stats.topTrendingCharacters.length} trending
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {stats.topTrendingCharacters.map((character, index) => (
                <div key={`trending-${character.id}-${index}`} className="relative bg-gradient-to-br from-orange-50 to-red-50 rounded-lg border-2 border-orange-200 p-4 hover:shadow-lg transition-all duration-200 hover:scale-105">
                  {/* Trending Badge */}
                  {character.isTrending && (
                    <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full animate-pulse">
                      🔥 HOT
                    </div>
                  )}
                  
                  <div className="flex items-start space-x-3">
                    <div className="w-12 h-16 bg-gradient-to-r from-orange-500 to-red-600 rounded-lg flex items-center justify-center text-white font-bold text-lg shrink-0">
                      {character.image ? (
                        <img 
                          src={character.image} 
                          alt={character.name}
                          className="w-full h-full object-cover rounded-lg border-2 border-white"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                            const nextEl = e.currentTarget.nextElementSibling as HTMLElement;
                            if (nextEl) nextEl.style.display = 'flex';
                          }}
                        />
                      ) : null}
                      <div className={character.image ? 'hidden' : 'flex items-center justify-center w-full h-full text-sm'}>
                        {character.gender === 'Female' ? '👩' : character.gender === 'Male' ? '👨' : '👤'}
                      </div>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1 mb-1">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          character.gender === 'Female' ? 'bg-pink-100 text-pink-800' :
                          character.gender === 'Male' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {character.gender}
                        </span>
                        
                        {/* Trending Arrow */}
                        {character.trendDirection && (
                          <span className={`text-sm ${
                            character.trendDirection === 'up' ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {character.trendDirection === 'up' ? '📈' : '📉'}
                          </span>
                        )}
                      </div>
                      
                      <h3 className="font-bold text-gray-900 text-sm mb-1 line-clamp-1">
                        {character.name}
                      </h3>
                      
                      <p className="text-xs text-gray-600 mb-2 line-clamp-1">
                        {character.animeName}
                      </p>
                      
                      <div className="space-y-1">
                        {/* Trend Percentage */}
                        {character.trendPercentage && (
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-gray-500">🔥 Trend:</span>
                            <span className={`font-bold ${
                              character.trendPercentage > 150 ? 'text-red-600' :
                              character.trendPercentage > 100 ? 'text-orange-600' : 'text-yellow-600'
                            }`}>
                              +{character.trendPercentage}%
                            </span>
                          </div>
                        )}
                        
                        {/* Favourites con indicatore visuale */}
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">Popolarità:</span>
                          <PopularityBadge score={character.favourites || 0} />
                        </div>
                        
                        {/* Barre di livello popolarità */}
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">Livello:</span>
                          <PopularityBars score={character.favourites || 0} />
                        </div>
                              return (
                                <div
                                  key={i}
                                  className={`w-2 h-3 rounded-sm ${
                                    isActive 
                                      ? i < 2 ? 'bg-green-400' : i < 4 ? 'bg-yellow-400' : 'bg-red-400'
                                      : 'bg-gray-200'
                                  }`}
                                />
                              );
                            })}
                          </div>
                        </div>
                        
                        {/* Numero formattato */}
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">Count:</span>
                          <span className="font-bold text-blue-600">
                            {character.favouritesFormatted || formatNumber(character.favourites || 0)}
                          </span>
                        </div>
                        
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">🎯 Score:</span>
                          <span className="font-bold text-purple-600">{character.cosplayScore || 0}</span>
                        </div>
                        
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">🎭 Diff:</span>
                          <span className={`font-bold ${
                            (character.cosplayDifficulty || 0) <= 3 ? 'text-green-600' :
                            (character.cosplayDifficulty || 0) <= 6 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            {character.cosplayDifficulty || 1}/10
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {character.description && (
                    <div className="mt-3 pt-3 border-t border-orange-200">
                      <p className="text-xs text-gray-600 line-clamp-2">
                        {character.description.length > 80 
                          ? `${character.description.substring(0, 80)}...` 
                          : character.description
                        }
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Anime Releases Grid */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              📺 Anime in Uscita
            </h2>
            <div className="flex space-x-4">
              <button
                onClick={syncAnimeReleases}
                disabled={syncing}
                className={`font-bold py-2 px-4 rounded-lg transition-colors ${
                  syncing
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {syncing ? '🔄 Sincronizzazione...' : '🔄 Sincronizza DB'}
              </button>
            </div>
          </div>

          {animeReleases.length === 0 ? (
            <div className="text-gray-500 text-center py-12">
              <div className="text-6xl mb-4">🎬</div>
              <p className="text-xl mb-2">Nessun anime release disponibile</p>
              <p className="text-sm">Usa il pulsante "Sync da AniList" per recuperare i dati più recenti</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {animeReleases.map((anime, index) => (
                <div key={anime.id || index} className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
                  <div className="flex items-start space-x-4">
                    {/* Cover Image or Placeholder */}
                    <div className="w-16 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-xl shrink-0">
                      {anime.coverImageLarge ? (
                        <img 
                          src={anime.coverImageLarge} 
                          alt={anime.title}
                          className="w-full h-full object-cover rounded-lg"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none';
                            const nextEl = e.currentTarget.nextElementSibling as HTMLElement;
                            if (nextEl) nextEl.style.display = 'flex';
                          }}
                        />
                      ) : null}
                      <div className={anime.coverImageLarge ? 'hidden' : 'flex items-center justify-center w-full h-full'}>
                        {anime.title.charAt(0)}
                      </div>
                    </div>
                    
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-gray-900 mb-2 truncate" title={anime.title}>
                        {anime.title}
                      </h3>
                      
                      {anime.titleEnglish && anime.titleEnglish !== anime.title && (
                        <p className="text-sm text-gray-600 mb-2 truncate" title={anime.titleEnglish}>
                          {anime.titleEnglish}
                        </p>
                      )}
                      
                      <div className="space-y-1 text-sm">
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(anime.status)}`}>
                            {anime.status}
                          </span>
                          <span className="text-gray-600">
                            {getSeasonEmoji(anime.season)} {anime.season} {anime.seasonYear}
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                          <div className="flex items-center space-x-1">
                            <span>📊</span>
                            <span className="font-medium">{formatNumber(anime.popularity)}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <span>⭐</span>
                            <span className="font-medium">{anime.meanScore || 'N/A'}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            {(() => {
                              const indicator = getPopularityIndicator(anime.favourites);
                              return (
                                <>
                                  <span className={indicator.color}>{indicator.icon}</span>
                                  <span className="font-medium">{formatNumber(anime.favourites)}</span>
                                </>
                              );
                            })()}
                          </div>
                          <div className="flex items-center space-x-1">
                            <span>📺</span>
                            <span className="font-medium">{anime.episodes || 'TBA'}</span>
                          </div>
                        </div>
                        
                        {anime.startDate && (
                          <div className="text-xs text-gray-500">
                            🗓️ Inizio: {formatDate(anime.startDate)}
                          </div>
                        )}
                        
                        {anime.genres && anime.genres.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {anime.genres.slice(0, 3).map((genre, i) => (
                              <span key={i} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">
                                {genre}
                              </span>
                            ))}
                            {anime.genres.length > 3 && (
                              <span className="text-gray-500 text-xs">+{anime.genres.length - 3}</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Characters Preview */}
                  {anime.characters && anime.characters.length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <h4 className="text-xs font-semibold text-gray-700 mb-2">
                        🎭 Personaggi Principali ({anime.characters.length})
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {anime.characters.slice(0, 3).map((char, i) => {
                          const indicator = getPopularityIndicator(char.favourites);
                          return (
                            <div key={`${anime.id}-char-${i}`} className="flex items-center space-x-2 bg-gray-50 rounded-lg px-2 py-1.5 min-w-0">
                              <span className={`w-2 h-2 rounded-full ${
                                char.isTrending ? 'bg-red-500 animate-pulse' :
                                char.hasGoogleTrends ? 'bg-orange-400' : 'bg-gray-400'
                              }`}></span>
                              
                              <div className="flex items-center space-x-1 min-w-0 flex-1">
                                <span className="text-xs font-medium text-gray-700 truncate max-w-16">
                                  {char.name}
                                </span>
                                <span className={`${indicator.color} text-xs`}>{indicator.icon}</span>
                                <span className="text-xs text-gray-500 font-medium">
                                  {formatNumber(char.favourites)}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                        {anime.characters.length > 3 && (
                          <span className="text-xs text-gray-500 px-2 py-1">
                            +{anime.characters.length - 3}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {anime.description && (
                    <div className="mt-3 pt-3 border-t">
                      <p className="text-xs text-gray-600 line-clamp-2">
                        {anime.description.length > 100 
                          ? `${anime.description.substring(0, 100)}...` 
                          : anime.description
                        }
                      </p>
                    </div>
                  )}
                  
                  {anime.anilistId && (
                    <div className="mt-3 pt-3 border-t">
                      <a
                        href={`https://anilist.co/anime/${anime.anilistId}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                      >
                        📖 Vedi su AniList →
                      </a>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

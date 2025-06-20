'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface SystemStats {
  totalCharacters: number;
  totalTrendData: number;
  recentTrendData: number;
  charactersWithTrends: number;
  avgTrendScore: number;
  lastUpdateDate?: string;
}

interface AnimeRelease {
  id: string;
  title?: string;
  popularity?: number;
  season?: string;
  seasonYear?: number;
  status?: string;
  startDate?: string;
  coverImageLarge?: string;
}

export default function AdminDashboard() {
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [animeReleases, setAnimeReleases] = useState<AnimeRelease[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSystemData();
  }, []);

  const fetchSystemData = async () => {
    try {
      setLoading(true);
      
      // Fetch system stats
      const statsResponse = await fetch('/api/admin/trends');
      const statsData = await statsResponse.json();
      setSystemStats(statsData.stats);
      
      // Fetch anime releases data
      const releasesResponse = await fetch('/api/admin/anime-releases');
      const releasesData = await releasesResponse.json();
      if (releasesData.success) {
        setAnimeReleases(releasesData.data || []);
      }
      
    } catch (error) {
      console.error('Error fetching system data:', error);
      setError('Errore nel caricamento dei dati');
    } finally {
      setLoading(false);
    }
  };

  const syncAnimeReleases = async () => {
    try {
      setSyncing(true);
      setError(null);
      
      const response = await fetch('/api/admin/anime-releases?action=sync');
      const result = await response.json();
      
      if (result.success) {
        alert(`Sync completato! ${result.stats.syncedAnime} anime sincronizzati, ${result.stats.syncedCharacters} personaggi aggiunti.`);
        await fetchSystemData(); // Refresh data
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

  const updateTrends = async () => {
    try {
      setSyncing(true);
      setError(null);
      
      const response = await fetch('/api/admin/trends', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'update-all' })
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert('Aggiornamento trend completato!');
        await fetchSystemData(); // Refresh data
      } else {
        setError(`Errore durante l'aggiornamento: ${result.error}`);
      }
      
    } catch (error) {
      console.error('Error updating trends:', error);
      setError('Errore durante l\'aggiornamento dei trend');
    } finally {
      setSyncing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-xl text-gray-600">Caricamento...</div>
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
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            🎯 CosplayRadar Admin Dashboard
          </h1>
          <p className="text-gray-600">
            Gestisci personaggi, trend e anime releases per anticipare i cosplay più popolari
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Stats Overview */}
        {systemStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="text-3xl mr-4">👥</div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Personaggi</h3>
                  <p className="text-2xl font-bold text-blue-600">{systemStats.totalCharacters}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="text-3xl mr-4">📈</div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Trend Data</h3>
                  <p className="text-2xl font-bold text-green-600">{systemStats.totalTrendData}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="text-3xl mr-4">⚡</div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Personaggi con Trend</h3>
                  <p className="text-2xl font-bold text-purple-600">{systemStats.charactersWithTrends}</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center">
                <div className="text-3xl mr-4">🎯</div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Score Medio</h3>
                  <p className="text-2xl font-bold text-orange-600">{Math.round(systemStats.avgTrendScore)}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">🔧 Azioni Sistema</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Link
              href="/admin/anilist-preview"
              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold py-3 px-6 rounded-lg transition-colors text-center"
            >
              🎯 AniList Preview
            </Link>
            
            <button
              onClick={syncAnimeReleases}
              disabled={syncing}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg transition-colors"
            >
              {syncing ? 'Sincronizzazione...' : '🎬 Sync Anime Releases'}
            </button>
            
            <button
              onClick={updateTrends}
              disabled={syncing}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg transition-colors"
            >
              {syncing ? 'Aggiornamento...' : '📈 Aggiorna Trend'}
            </button>
            
            <Link
              href="/admin/sync"
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-lg transition-colors text-center"
            >
              🔄 Gestione Sync
            </Link>
          </div>
        </div>

        {/* Anime Releases */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            🎬 Anime Releases ({animeReleases.length})
          </h2>
          
          {animeReleases.length === 0 ? (
            <div className="text-gray-500 text-center py-8">
              <p>Nessun dato di anime releases disponibile.</p>
              <p className="text-sm mt-2">Usa il pulsante "Sync Anime Releases" per recuperare i dati da AniList.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {animeReleases.slice(0, 9).map((anime, index) => (
                <div key={anime.id || index} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-lg">
                      {anime.title?.charAt(0) || '?'}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 truncate">
                        {anime.title || 'Anime Title'}
                      </h3>
                      <div className="text-sm text-gray-600">
                        <p>Popolarità: {anime.popularity || 0}</p>
                        <p>Season: {anime.season} {anime.seasonYear}</p>
                        <p>Status: {anime.status}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Links */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">🔗 Collegamenti Rapidi</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link
              href="/api/trends?limit=10"
              target="_blank"
              className="bg-gray-100 hover:bg-gray-200 p-4 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">📊</div>
              <div className="font-semibold">API Trends</div>
            </Link>
            
            <Link
              href="/api/market-analysis?type=market-overview"
              target="_blank"
              className="bg-gray-100 hover:bg-gray-200 p-4 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">📈</div>
              <div className="font-semibold">Market Analysis</div>
            </Link>
            
            <Link
              href="/dashboard"
              className="bg-gray-100 hover:bg-gray-200 p-4 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">🎯</div>
              <div className="font-semibold">Dashboard</div>
            </Link>
            
            <Link
              href="/"
              className="bg-gray-100 hover:bg-gray-200 p-4 rounded-lg text-center transition-colors"
            >
              <div className="text-2xl mb-2">🏠</div>
              <div className="font-semibold">Home</div>
            </Link>
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Last Update: {systemStats?.lastUpdateDate ? new Date(systemStats.lastUpdateDate).toLocaleString('it-IT') : 'N/A'}</p>
          <p className="mt-1">Sistema di monitoraggio trend per cosplay basato su AniList, Jikan API e Google Trends</p>
        </div>
      </div>
    </div>
  );
}

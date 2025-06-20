'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Character {
  id: number;
  name: {
    full: string;
    native?: string;
  };
  image?: {
    large?: string;
    medium?: string;
  };
  favourites: number;
  gender: string;
  anime: {
    title: string;
    popularity: number;
    status: string;
  };
}

interface AniListData {
  success: boolean;
  stats: {
    totalAnime: number;
    totalAvailable: number;
    totalCharacters: number;
    avgPopularity: number;
    statusDistribution: Record<string, number>;
    formatDistribution: Record<string, number>;
  };
  topCharacters: Character[];
  data: any[];
}

export default function AniListPreviewPage() {
  const [data, setData] = useState<AniListData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAniListData();
  }, []);

  const fetchAniListData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/anilist-preview');
      const result = await response.json();
      
      if (result.success) {
        setData(result);
      } else {
        setError(result.error || 'Errore nel caricamento dei dati');
      }
    } catch (error) {
      console.error('Error fetching AniList data:', error);
      setError('Errore nella connessione al server');
    } finally {
      setLoading(false);
    }
  };

  const getGenderEmoji = (gender: string) => {
    switch (gender?.toLowerCase()) {
      case 'female': return '👩';
      case 'male': return '👨';
      default: return '👤';
    }
  };

  const getGenderColor = (gender: string) => {
    switch (gender?.toLowerCase()) {
      case 'female': return 'bg-pink-100 text-pink-800';
      case 'male': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}k`;
    }
    return num.toString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-xl text-gray-600">Caricamento dati AniList...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error || 'Errore nel caricamento dei dati'}
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
                🎯 AniList Preview - Estate 2025
              </h1>
              <p className="text-gray-600">
                Anticipa i trend cosplay con i dati live da AniList
              </p>
              <p className="text-sm text-green-600 mt-2">
                ✅ Dati aggiornati in tempo reale - {data.stats.totalAnime} anime, {data.stats.totalCharacters} personaggi
              </p>
            </div>
            <Link
              href="/admin"
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition-colors"
            >
              ← Dashboard
            </Link>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl mr-4">🎬</div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Anime Estate</h3>
                <p className="text-2xl font-bold text-blue-600">{data.stats.totalAnime}</p>
                <p className="text-xs text-gray-500">di {formatNumber(data.stats.totalAvailable)} totali</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl mr-4">👥</div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Personaggi</h3>
                <p className="text-2xl font-bold text-green-600">{data.stats.totalCharacters}</p>
                <p className="text-xs text-green-600">Disponibili per trend</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl mr-4">📈</div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Avg Popularity</h3>
                <p className="text-2xl font-bold text-purple-600">{formatNumber(data.stats.avgPopularity)}</p>
                <p className="text-xs text-gray-500">Media molto alta</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="text-3xl mr-4">🎯</div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Format</h3>
                <p className="text-sm text-gray-600">
                  📺 {data.stats.formatDistribution.TV || 0} Serie
                </p>
                <p className="text-sm text-gray-600">
                  🎬 {data.stats.formatDistribution.MOVIE || 0} Film
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Top Characters for Cosplay */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            🏆 Top Characters per Cosplay - Estate 2025
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.topCharacters.slice(0, 12).map((character, index) => (
              <div key={character.id || index} className="border rounded-lg p-4 hover:shadow-lg transition-shadow bg-gradient-to-br from-white to-gray-50">
                <div className="flex items-start space-x-4">
                  {/* Character Image */}
                  <div className="w-16 h-20 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg flex items-center justify-center text-white font-bold text-xl shrink-0">
                    {character.image?.large ? (
                      <img 
                        src={character.image.large} 
                        alt={character.name.full}
                        className="w-full h-full object-cover rounded-lg"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          const nextEl = e.currentTarget.nextElementSibling as HTMLElement;
                          if (nextEl) nextEl.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div className={character.image?.large ? 'hidden' : 'flex items-center justify-center w-full h-full'}>
                      {getGenderEmoji(character.gender)}
                    </div>
                  </div>
                  
                  {/* Character Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="bg-yellow-100 text-yellow-800 text-xs font-bold px-2 py-1 rounded">
                        #{index + 1}
                      </span>
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${getGenderColor(character.gender)}`}>
                        {character.gender}
                      </span>
                    </div>
                    
                    <h3 className="font-bold text-gray-900 mb-1 text-sm line-clamp-2">
                      {character.name.full}
                    </h3>
                    
                    <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                      {character.anime.title}
                    </p>
                    
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500">❤️ Favoriti:</span>
                        <span className="font-bold text-red-600">{formatNumber(character.favourites)}</span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-500">📊 Anime Pop:</span>
                        <span className="font-bold text-blue-600">{formatNumber(character.anime.popularity)}</span>
                      </div>
                    </div>
                    
                    {/* Cosplay Potential Score */}
                    <div className="mt-3 pt-2 border-t">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-gray-500">Potenziale Cosplay:</span>
                        <div className="flex items-center space-x-1">
                          {Array.from({ length: 5 }, (_, i) => (
                            <span 
                              key={i} 
                              className={`text-xs ${
                                i < Math.min(Math.ceil(character.favourites / 4000), 5) 
                                  ? 'text-yellow-400' 
                                  : 'text-gray-300'
                              }`}
                            >
                              ⭐
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">⚡ Azioni Rapide</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={fetchAniListData}
              className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
            >
              🔄 Aggiorna Dati
            </button>
            
            <Link
              href="/api/anilist-preview"
              target="_blank"
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors text-center"
            >
              📊 Vedi API Raw
            </Link>
            
            <Link
              href="/admin/anime-releases"
              className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors text-center"
            >
              🎬 Gestione Releases
            </Link>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Dati aggiornati in tempo reale da AniList GraphQL API</p>
          <p className="mt-1">Sistema di anticipazione trend per cosplayer - Estate 2025</p>
        </div>
      </div>
    </div>
  );
}

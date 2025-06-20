'use client';

import { useEffect, useState } from 'react';

interface Character {
  id: string;
  name: string;
  series: string;
  gender?: string;
  source: string;
  imageUrl?: string;
  popularityScore: number;
}

export default function TestAniListPage() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<'all' | 'anilist' | 'jikan'>('anilist');
  const [gender, setGender] = useState<string>('all');

  const fetchCharacters = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        source,
        limit: '10',
        page: '1',
      });
      
      if (gender !== 'all') {
        params.append('gender', gender);
      }
      
      const response = await fetch(`/api/characters?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setCharacters(data.characters || []);
      
      console.log('API Response:', data);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharacters();
  }, [source, gender]);

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">🧪 AniList Integration Test</h1>
      
      {/* Controlli */}
      <div className="mb-6 space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Source:</label>
          <select 
            value={source}
            onChange={(e) => setSource(e.target.value as any)}
            className="border rounded px-3 py-2"
          >
            <option value="all">All Sources</option>
            <option value="anilist">AniList Only</option>
            <option value="jikan">Jikan Only</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium mb-2">Gender:</label>
          <select 
            value={gender}
            onChange={(e) => setGender(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="all">All Genders</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Non-binary">Non-binary</option>
          </select>
        </div>
        
        <button 
          onClick={fetchCharacters}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Stato */}
      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading characters...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Risultati */}
      {!loading && !error && (
        <div>
          <h2 className="text-xl font-semibold mb-4">
            Found {characters.length} characters
          </h2>
          
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {characters.map((character) => (
              <div key={character.id} className="border rounded-lg p-4 shadow-sm">
                {character.imageUrl && (
                  <img 
                    src={character.imageUrl}
                    alt={character.name}
                    className="w-full h-48 object-cover rounded mb-3"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                )}
                
                <h3 className="font-semibold text-lg">{character.name}</h3>
                <p className="text-gray-600 mb-2">{character.series}</p>
                
                <div className="text-sm space-y-1">
                  <div>
                    <span className="font-medium">Gender:</span> {character.gender || 'Unknown'}
                  </div>
                  <div>
                    <span className="font-medium">Source:</span> 
                    <span className={`ml-1 px-2 py-1 rounded text-xs ${
                      character.source === 'anilist' ? 'bg-purple-100 text-purple-800' :
                      character.source === 'jikan' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {character.source}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">Popularity:</span> {character.popularityScore}
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {characters.length === 0 && (
            <p className="text-gray-500 text-center py-8">
              No characters found with current filters.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

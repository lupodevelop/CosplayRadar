'use client';

import { useState } from 'react';

interface SyncResult {
  success: boolean;
  syncedCount: number;
  updatedCount: number;
  errors: string[];
  sources?: {
    jikan?: any;
    anilist?: any;
  };
}

interface SyncStats {
  totalCharacters: number;
  anilistCharacters?: number;
  jikanCharacters?: number;
  recentTrends: number;
  lastSyncDate: string;
}

export default function TestSyncPage() {
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [syncStats, setSyncStats] = useState<SyncStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performSync = async (source: 'all' | 'anilist' | 'jikan') => {
    setLoading(true);
    setError(null);
    setSyncResult(null);
    
    try {
      const response = await fetch('/api/admin/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'sync',
          source: source === 'all' ? undefined : source,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      setSyncResult(result);
      console.log('Sync result:', result);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Sync error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStats = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/admin/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'status',
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      setSyncStats(result.stats);
      console.log('Stats:', result);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Stats error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">🔧 Sync Administration Test</h1>
      
      {/* Controlli */}
      <div className="mb-6 space-y-4">
        <div className="flex gap-4">
          <button 
            onClick={() => performSync('anilist')}
            disabled={loading}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50"
          >
            🔄 Sync AniList
          </button>
          
          <button 
            onClick={() => performSync('jikan')}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            🔄 Sync Jikan
          </button>
          
          <button 
            onClick={() => performSync('all')}
            disabled={loading}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
          >
            🔄 Sync All
          </button>
          
          <button 
            onClick={getStats}
            disabled={loading}
            className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 disabled:opacity-50"
          >
            📊 Get Stats
          </button>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Processing...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Sync Result */}
      {syncResult && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">Sync Results</h2>
          
          <div className={`border rounded-lg p-4 ${
            syncResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
          }`}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <span className="font-medium">Status:</span>
                <span className={`ml-2 px-2 py-1 rounded text-sm ${
                  syncResult.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {syncResult.success ? 'Success' : 'Failed'}
                </span>
              </div>
              <div>
                <span className="font-medium">Synced:</span> {syncResult.syncedCount}
              </div>
              <div>
                <span className="font-medium">Updated:</span> {syncResult.updatedCount}
              </div>
            </div>

            {syncResult.errors.length > 0 && (
              <div>
                <h3 className="font-medium text-red-700 mb-2">Errors:</h3>
                <ul className="list-disc list-inside text-sm text-red-600 space-y-1">
                  {syncResult.errors.map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            )}

            {syncResult.sources && (
              <div className="mt-4">
                <h3 className="font-medium mb-2">Source Details:</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  {syncResult.sources.jikan && (
                    <div className="bg-blue-50 p-3 rounded">
                      <h4 className="font-medium text-blue-800">Jikan</h4>
                      <p>Synced: {syncResult.sources.jikan.syncedCount}</p>
                      <p>Updated: {syncResult.sources.jikan.updatedCount}</p>
                    </div>
                  )}
                  {syncResult.sources.anilist && (
                    <div className="bg-purple-50 p-3 rounded">
                      <h4 className="font-medium text-purple-800">AniList</h4>
                      <p>Synced: {syncResult.sources.anilist.syncedCount}</p>
                      <p>Updated: {syncResult.sources.anilist.updatedCount}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Stats */}
      {syncStats && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Database Statistics</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-800">Total Characters</h3>
              <p className="text-2xl font-bold text-blue-900">{syncStats.totalCharacters}</p>
            </div>
            
            {syncStats.anilistCharacters !== undefined && (
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <h3 className="font-medium text-purple-800">AniList Characters</h3>
                <p className="text-2xl font-bold text-purple-900">{syncStats.anilistCharacters}</p>
              </div>
            )}
            
            {syncStats.jikanCharacters !== undefined && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-medium text-green-800">Jikan Characters</h3>
                <p className="text-2xl font-bold text-green-900">{syncStats.jikanCharacters}</p>
              </div>
            )}
            
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="font-medium text-gray-800">Recent Trends</h3>
              <p className="text-2xl font-bold text-gray-900">{syncStats.recentTrends}</p>
            </div>
          </div>
          
          <div className="mt-4 text-sm text-gray-600">
            Last sync: {new Date(syncStats.lastSyncDate).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  );
}

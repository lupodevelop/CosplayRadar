/**
 * Pagina Admin per gestire la sincronizzazione dei personaggi
 */

'use client';

import { useState, useEffect } from 'react';

interface SyncStatus {
  isRunning: boolean;
}

interface SyncStats {
  totalCharacters: number;
  recentTrends: number;
  lastSyncDate?: string;
}

interface SyncResult {
  success: boolean;
  syncedCount: number;
  updatedCount: number;
  errors: string[];
}

export default function AdminSyncPage() {
  const [status, setStatus] = useState<SyncStatus>({ isRunning: false });
  const [stats, setStats] = useState<SyncStats | null>(null);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [jikanData, setJikanData] = useState<any>(null);

  useEffect(() => {
    fetchSyncStatus();
  }, []);

  const fetchSyncStatus = async () => {
    try {
      const response = await fetch('/api/admin/sync');
      const data = await response.json();
      setStatus(data.status);
      setStats(data.stats);
    } catch (error) {
      console.error('Error fetching sync status:', error);
    }
  };

  const startSync = async () => {
    setLoading(true);
    setSyncResult(null);
    
    try {
      const response = await fetch('/api/admin/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action: 'sync' }),
      });
      
      const result = await response.json();
      setSyncResult(result);
      
      // Aggiorna lo stato
      await fetchSyncStatus();
    } catch (error) {
      console.error('Error starting sync:', error);
      setSyncResult({
        success: false,
        syncedCount: 0,
        updatedCount: 0,
        errors: [`Network error: ${error}`],
      });
    } finally {
      setLoading(false);
    }
  };

  const cleanOldData = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/admin/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action: 'clean' }),
      });
      
      const result = await response.json();
      alert(`Cleaned ${result.cleanedCount} old trend records`);
      
      await fetchSyncStatus();
    } catch (error) {
      console.error('Error cleaning data:', error);
      alert('Error cleaning old data');
    } finally {
      setLoading(false);
    }
  };

  const testJikanAPI = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/jikan/characters?page=1');
      const data = await response.json();
      setJikanData(data);
    } catch (error) {
      console.error('Error testing Jikan API:', error);
      setJikanData({ error: 'Failed to fetch data' });
    } finally {
      setLoading(false);
    }
  };

  const clearJikanCache = async () => {
    try {
      const response = await fetch('/api/jikan/characters', {
        method: 'DELETE',
      });
      const result = await response.json();
      alert(result.message);
    } catch (error) {
      console.error('Error clearing cache:', error);
      alert('Error clearing cache');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Admin - Character Sync</h1>
      
      {/* Status Section */}
      <div className="mb-8 p-6 bg-white rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Sync Status</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="p-4 bg-gray-50 rounded">
            <div className="text-sm text-gray-600">Status</div>
            <div className={`font-semibold ${status.isRunning ? 'text-yellow-600' : 'text-green-600'}`}>
              {status.isRunning ? 'Running' : 'Idle'}
            </div>
          </div>
          
          {stats && (
            <>
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-600">Total Characters</div>
                <div className="font-semibold text-blue-600">{stats.totalCharacters}</div>
              </div>
              
              <div className="p-4 bg-gray-50 rounded">
                <div className="text-sm text-gray-600">Recent Trends</div>
                <div className="font-semibold text-purple-600">{stats.recentTrends}</div>
              </div>
            </>
          )}
        </div>
        
        {stats?.lastSyncDate && (
          <div className="text-sm text-gray-600">
            Last sync: {new Date(stats.lastSyncDate).toLocaleString()}
          </div>
        )}
      </div>

      {/* Actions Section */}
      <div className="mb-8 p-6 bg-white rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Actions</h2>
        
        <div className="flex flex-wrap gap-4">
          <button
            onClick={startSync}
            disabled={loading || status.isRunning}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Running...' : 'Start Sync'}
          </button>
          
          <button
            onClick={cleanOldData}
            disabled={loading}
            className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
          >
            Clean Old Data
          </button>
          
          <button
            onClick={testJikanAPI}
            disabled={loading}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            Test Jikan API
          </button>
          
          <button
            onClick={clearJikanCache}
            disabled={loading}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
          >
            Clear Cache
          </button>
          
          <button
            onClick={fetchSyncStatus}
            disabled={loading}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
          >
            Refresh Status
          </button>
        </div>
      </div>

      {/* Sync Result Section */}
      {syncResult && (
        <div className="mb-8 p-6 bg-white rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Last Sync Result</h2>
          
          <div className={`p-4 rounded ${syncResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <div className="flex items-center mb-2">
              <span className={`w-3 h-3 rounded-full mr-2 ${syncResult.success ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span className="font-semibold">
                {syncResult.success ? 'Success' : 'Failed'}
              </span>
            </div>
            
            <div className="text-sm space-y-1">
              <div>Synced: {syncResult.syncedCount} characters</div>
              <div>Updated: {syncResult.updatedCount} characters</div>
              {syncResult.errors.length > 0 && (
                <div>
                  <div className="font-semibold text-red-600 mt-2">Errors:</div>
                  <ul className="list-disc list-inside text-red-600">
                    {syncResult.errors.map((error, index) => (
                      <li key={index} className="text-xs">{error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Jikan API Test Result */}
      {jikanData && (
        <div className="mb-8 p-6 bg-white rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Jikan API Test Result</h2>
          
          {jikanData.error ? (
            <div className="p-4 bg-red-50 border border-red-200 rounded">
              <div className="text-red-600 font-semibold">Error</div>
              <div className="text-red-500 text-sm">{jikanData.error}</div>
            </div>
          ) : (
            <div>
              <div className="mb-4 text-sm text-gray-600">
                Found {jikanData.characters?.length || 0} characters
              </div>
              
              {jikanData.characters?.slice(0, 3).map((character: any) => (
                <div key={character.id} className="flex items-center space-x-4 p-3 border rounded mb-2">
                  <img
                    src={character.imageUrl}
                    alt={character.name}
                    className="w-12 h-12 object-cover rounded"
                  />
                  <div>
                    <div className="font-semibold">{character.name}</div>
                    <div className="text-sm text-gray-600">
                      {character.series} • {character.favorites} favorites
                    </div>
                  </div>
                </div>
              ))}
              
              <details className="mt-4">
                <summary className="cursor-pointer text-blue-600 hover:text-blue-800">
                  Show full response
                </summary>
                <pre className="mt-2 p-4 bg-gray-100 rounded text-xs overflow-auto max-h-96">
                  {JSON.stringify(jikanData, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

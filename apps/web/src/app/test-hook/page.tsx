// Test hook isolato
'use client';

import { usePopularityIndicator, usePopularityTiers } from '@/hooks/use-popularity';

export default function TestHookPage() {
  const { tiers, loading } = usePopularityTiers();
  
  // Test con valori specifici che sappiamo essere nel dataset
  const testScore1 = 73809; // Dovrebbe essere ELITE
  const testScore2 = 65993; // Dovrebbe essere POPULAR
  const testScore3 = 39846; // Dovrebbe essere POPULAR (threshold)
  const testScore4 = 27837; // Dovrebbe essere KNOWN (threshold)
  const testScore5 = 5000;  // Dovrebbe essere FRESH
  
  const indicator1 = usePopularityIndicator(testScore1);
  const indicator2 = usePopularityIndicator(testScore2);
  const indicator3 = usePopularityIndicator(testScore3);
  const indicator4 = usePopularityIndicator(testScore4);
  const indicator5 = usePopularityIndicator(testScore5);

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-2xl font-bold mb-4">🧪 Test Hook Isolato</h1>
      
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-2">📊 Tiers Status</h2>
        <p>Loading: {loading ? 'Yes' : 'No'}</p>
        <pre className="bg-gray-100 p-4 rounded text-sm">
          {JSON.stringify(tiers, null, 2)}
        </pre>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">🏷️ Test Specifici</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-white rounded-lg shadow">
            <div>
              <h3 className="font-semibold">Test Score: {testScore1.toLocaleString()}</h3>
              <p className="text-sm text-gray-600">Dovrebbe essere ELITE</p>
            </div>
            <div className="text-right">
              <div className="text-sm">{indicator1.icon} {indicator1.level}</div>
              <div className="text-xs text-gray-500">{indicator1.color}</div>
            </div>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-white rounded-lg shadow">
            <div>
              <h3 className="font-semibold">Test Score: {testScore2.toLocaleString()}</h3>
              <p className="text-sm text-gray-600">Dovrebbe essere POPULAR</p>
            </div>
            <div className="text-right">
              <div className="text-sm">{indicator2.icon} {indicator2.level}</div>
              <div className="text-xs text-gray-500">{indicator2.color}</div>
            </div>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-white rounded-lg shadow">
            <div>
              <h3 className="font-semibold">Test Score: {testScore3.toLocaleString()}</h3>
              <p className="text-sm text-gray-600">Dovrebbe essere POPULAR (threshold)</p>
            </div>
            <div className="text-right">
              <div className="text-sm">{indicator3.icon} {indicator3.level}</div>
              <div className="text-xs text-gray-500">{indicator3.color}</div>
            </div>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-white rounded-lg shadow">
            <div>
              <h3 className="font-semibold">Test Score: {testScore4.toLocaleString()}</h3>
              <p className="text-sm text-gray-600">Dovrebbe essere KNOWN (threshold)</p>
            </div>
            <div className="text-right">
              <div className="text-sm">{indicator4.icon} {indicator4.level}</div>
              <div className="text-xs text-gray-500">{indicator4.color}</div>
            </div>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-white rounded-lg shadow">
            <div>
              <h3 className="font-semibold">Test Score: {testScore5.toLocaleString()}</h3>
              <p className="text-sm text-gray-600">Dovrebbe essere FRESH</p>
            </div>
            <div className="text-right">
              <div className="text-sm">{indicator5.icon} {indicator5.level}</div>
              <div className="text-xs text-gray-500">{indicator5.color}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

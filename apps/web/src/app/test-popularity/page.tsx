// Test page per debug del popularity system
'use client';

import { usePopularityIndicator, usePopularityTiers } from '@/hooks/use-popularity';
import { PopularityBadge } from '@/components/popularity-indicators';

export default function TestPopularityPage() {
  const { tiers, loading } = usePopularityTiers();
  
  // Test characters con valori reali
  const testCharacters = [
    { name: 'Lelouch Lamperouge', popularity: 174158 },
    { name: 'Luffy Monkey D.', popularity: 144366 },
    { name: 'Levi', popularity: 143715 },
    { name: 'L Lawliet', popularity: 128641 },
    { name: 'Naruto Uzumaki', popularity: 85780 },
    { name: 'Character medio', popularity: 40000 },
    { name: 'Character basso', popularity: 20000 },
    { name: 'Character nuovo', popularity: 5000 }
  ];

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-2xl font-bold mb-4">🧪 Test Popularity System</h1>
      
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-2">📊 Tiers Status</h2>
        <p>Loading: {loading ? 'Yes' : 'No'}</p>
        <pre className="bg-gray-100 p-4 rounded text-sm">
          {JSON.stringify(tiers, null, 2)}
        </pre>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">🏷️ Badge Test</h2>
        <div className="space-y-4">
          {testCharacters.map((char) => {
            const indicator = usePopularityIndicator(char.popularity);
            return (
              <div key={char.name} className="flex items-center justify-between p-4 bg-white rounded-lg shadow">
                <div>
                  <h3 className="font-semibold">{char.name}</h3>
                  <p className="text-sm text-gray-600">Popularity: {char.popularity.toLocaleString()}</p>
                </div>
                <div className="flex items-center gap-4">
                  <PopularityBadge score={char.popularity} />
                  <div className="text-right">
                    <div className="text-sm">{indicator.icon} {indicator.level}</div>
                    <div className="text-xs text-gray-500">{indicator.color}</div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

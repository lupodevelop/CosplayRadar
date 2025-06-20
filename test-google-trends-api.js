// Test semplice per Google Trends API
const testGoogleTrendsAPI = async () => {
  console.log('Testing Google Trends API...');
  
  try {
    // Test 1: Status dell'API sync
    console.log('\n1. Testing sync status...');
    const syncResponse = await fetch('http://localhost:3000/api/admin/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'status' })
    });
    const syncData = await syncResponse.json();
    console.log('Sync status:', syncData);

    // Test 2: Status Google Trends
    console.log('\n2. Testing Google Trends status...');
    const trendsResponse = await fetch('http://localhost:3000/api/admin/trends', {
      method: 'GET'
    });
    const trendsData = await trendsResponse.json();
    console.log('Trends status:', trendsData);

    // Test 3: Trends query API
    console.log('\n3. Testing trends query...');
    const queryResponse = await fetch('http://localhost:3000/api/trends?limit=5');
    const queryData = await queryResponse.json();
    console.log('Trends query:', queryData);

    // Test 4: Market analysis
    console.log('\n4. Testing market analysis...');
    const marketResponse = await fetch('http://localhost:3000/api/market-analysis?type=market-overview&limit=5');
    const marketData = await marketResponse.json();
    console.log('Market analysis:', marketData);

  } catch (error) {
    console.error('Test failed:', error);
  }
};

testGoogleTrendsAPI();

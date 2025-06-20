// Test per popolare dati di test
const testPopulateData = async () => {
  console.log('=== Populating Test Trend Data ===\n');
  
  try {
    // Popola dati di test
    console.log('1. Populating test data...');
    const populateResponse = await fetch('http://localhost:3000/api/admin/test-data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        action: 'populate-test-data',
        count: 15 // 15 personaggi
      })
    });
    
    const populateData = await populateResponse.json();
    console.log('Populate Result:', JSON.stringify(populateData, null, 2));
    
    console.log('\n2. Checking status after population...');
    
    // Status delle trends
    const statusResponse = await fetch('http://localhost:3000/api/admin/trends');
    const statusData = await statusResponse.json();
    console.log('Trends Status:', JSON.stringify(statusData, null, 2));
    
    console.log('\n3. Query trends with data...');
    
    // Query trends
    const trendsResponse = await fetch('http://localhost:3000/api/trends?limit=5');
    const trendsData = await trendsResponse.json();
    console.log('Trends Query:', JSON.stringify(trendsData, null, 2));
    
    console.log('\n4. Market analysis with data...');
    
    // Market analysis
    const marketResponse = await fetch('http://localhost:3000/api/market-analysis?type=market-overview&limit=5');
    const marketData = await marketResponse.json();
    console.log('Market Analysis:', JSON.stringify(marketData, null, 2));
    
  } catch (error) {
    console.error('Test failed:', error);
  }
};

testPopulateData();

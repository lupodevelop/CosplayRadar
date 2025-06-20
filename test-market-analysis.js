// Test per l'analisi di mercato
const testMarketAnalysis = async () => {
  console.log('=== Testing Market Analysis API ===\n');
  
  try {
    // Test 1: Market Overview
    console.log('1. Testing Market Overview...');
    const overviewResponse = await fetch('http://localhost:3000/api/market-analysis?type=market-overview&limit=5');
    const overviewData = await overviewResponse.json();
    console.log('Market Overview:', JSON.stringify(overviewData, null, 2));
    
    console.log('\n---\n');
    
    // Test 2: Top Cosplay Trends
    console.log('2. Testing Top Cosplay Trends...');
    const cosplayResponse = await fetch('http://localhost:3000/api/market-analysis?type=top-cosplay&limit=5');
    const cosplayData = await cosplayResponse.json();
    console.log('Top Cosplay:', JSON.stringify(cosplayData, null, 2));
    
    console.log('\n---\n');
    
    // Test 3: Market Gaps
    console.log('3. Testing Market Gaps...');
    const gapsResponse = await fetch('http://localhost:3000/api/market-analysis?type=market-gaps&limit=10');
    const gapsData = await gapsResponse.json();
    console.log('Market Gaps:', JSON.stringify(gapsData, null, 2));
    
  } catch (error) {
    console.error('Market analysis test failed:', error);
  }
};

testMarketAnalysis();

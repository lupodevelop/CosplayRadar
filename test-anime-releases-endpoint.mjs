import fetch from 'node-fetch';

async function testAnimeReleasesEndpoint() {
  console.log('🎯 ====== TESTING ANIME RELEASES ENDPOINT ======');
  
  try {
    // Test 1: Lista anime releases
    console.log('\n📊 Testing GET /api/admin/anime-releases...');
    const listResponse = await fetch('http://localhost:3000/api/admin/anime-releases');
    const listResult = await listResponse.json();
    console.log('Status:', listResponse.status);
    console.log('List Response:', JSON.stringify(listResult, null, 2));
    
    // Test 2: Sync anime releases
    console.log('\n🔄 Testing GET /api/admin/anime-releases?action=sync...');
    const syncResponse = await fetch('http://localhost:3000/api/admin/anime-releases?action=sync');
    const syncResult = await syncResponse.json();
    console.log('Status:', syncResponse.status);
    console.log('Sync Response:', JSON.stringify(syncResult, null, 2));
    
    // Test 3: Lista dopo sync
    console.log('\n📊 Testing list after sync...');
    const listAfterResponse = await fetch('http://localhost:3000/api/admin/anime-releases');
    const listAfterResult = await listAfterResponse.json();
    console.log('Status:', listAfterResponse.status);
    console.log('List After Response:', JSON.stringify(listAfterResult, null, 2));
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testAnimeReleasesEndpoint();

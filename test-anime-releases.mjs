import fetch from 'node-fetch';

async function testAnimeReleases() {
  console.log('🎯 ====== TESTING ANIME RELEASES ======');
  
  try {
    console.log('\n📊 Triggering anime release sync...');
    const response = await fetch('http://localhost:3000/api/admin/sync', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        action: 'full-sync'
      })
    });
    
    const result = await response.json();
    console.log('Status:', response.status);
    console.log('Response:', JSON.stringify(result, null, 2));
    
    // Aspetta un po' per il sync
    console.log('\n⏳ Waiting for sync to complete...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Controlla i risultati
    console.log('\n📈 Checking results...');
    const statusResponse = await fetch('http://localhost:3000/api/admin/sync');
    const statusResult = await statusResponse.json();
    console.log('Final Status:', JSON.stringify(statusResult, null, 2));
    
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

testAnimeReleases();

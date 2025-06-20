// Test per aggiornare Google Trends per alcuni personaggi
const testTrendsUpdate = async () => {
  console.log('=== Testing Google Trends Update ===\n');
  
  try {
    // Prima ottieni alcuni personaggi
    console.log('1. Getting characters...');
    const charactersResponse = await fetch('http://localhost:3000/api/characters?limit=3');
    const charactersData = await charactersResponse.json();
    
    if (charactersData.characters && charactersData.characters.length > 0) {
      const characterIds = charactersData.characters.map(c => c.id);
      console.log('Found characters:', charactersData.characters.map(c => c.name));
      
      // Test update per questi personaggi
      console.log('\n2. Updating Google Trends for these characters...');
      const updateResponse = await fetch('http://localhost:3000/api/admin/trends', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          action: 'update-batch',
          characterIds: characterIds.slice(0, 2) // Solo i primi 2 per il test
        })
      });
      
      const updateData = await updateResponse.json();
      console.log('Update result:', JSON.stringify(updateData, null, 2));
      
      // Attendi un po' per i rate limits
      console.log('\n3. Waiting 10 seconds...');
      await new Promise(resolve => setTimeout(resolve, 10000));
      
      // Check status dopo l'update
      console.log('\n4. Checking status after update...');
      const statusResponse = await fetch('http://localhost:3000/api/admin/trends');
      const statusData = await statusResponse.json();
      console.log('Status after update:', JSON.stringify(statusData, null, 2));
      
    } else {
      console.log('No characters found');
    }
    
  } catch (error) {
    console.error('Test failed:', error);
  }
};

testTrendsUpdate();

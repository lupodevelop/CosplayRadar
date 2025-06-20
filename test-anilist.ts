import { anilistService } from './apps/web/src/services/anilistService';

async function testAniListBasic() {
  console.log('🧪 Testing basic AniList service functionality...');
  
  try {
    // Test semplice per verificare che il servizio sia disponibile
    const result = await anilistService.getTopCharacters({ page: 1, perPage: 2 });
    console.log('✅ AniList service is working!');
    console.log(`Found ${result.characters.length} characters`);
    
    if (result.characters.length > 0) {
      const char = result.characters[0];
      console.log('First character:');
      console.log(`  Name: ${char.name}`);
      console.log(`  Series: ${char.series}`);
      console.log(`  Gender: ${char.gender}`);
      console.log(`  Source: ${char.source}`);
    }
    
    return true;
  } catch (error) {
    console.error('❌ AniList service test failed:', error.message);
    return false;
  }
}

testAniListBasic().then(success => {
  process.exit(success ? 0 : 1);
});

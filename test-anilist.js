#!/usr/bin/env node

// Test script per verificare l'AniList service
const { anilistService } = require('./apps/web/src/services/anilistService');

async function testAniListService() {
  console.log('🧪 Testing AniList Service...\n');

  try {
    // Test 1: Ottieni personaggi top
    console.log('📋 Testing getTopCharacters...');
    const topCharacters = await anilistService.getTopCharacters({ page: 1, perPage: 5 });
    console.log(`✅ Found ${topCharacters.characters.length} top characters`);
    console.log('First character:', {
      name: topCharacters.characters[0]?.name,
      series: topCharacters.characters[0]?.series,
      gender: topCharacters.characters[0]?.gender,
      source: topCharacters.characters[0]?.source,
    });

    // Test 2: Ottieni personaggi per genere
    console.log('\n🚺 Testing getTopCharacters with gender filter...');
    const femaleCharacters = await anilistService.getTopCharacters({ 
      gender: 'Female', 
      page: 1, 
      perPage: 3 
    });
    console.log(`✅ Found ${femaleCharacters.characters.length} female characters`);
    femaleCharacters.characters.forEach(char => {
      console.log(`  - ${char.name} (${char.series}) - Gender: ${char.gender}`);
    });

    // Test 3: Ottieni personaggi trending settimanali
    console.log('\n📈 Testing getWeeklyTrendingCharacters...');
    const trendingCharacters = await anilistService.getWeeklyTrendingCharacters({ 
      page: 1, 
      perPage: 5 
    });
    console.log(`✅ Found ${trendingCharacters.characters.length} weekly trending characters`);
    console.log('First trending character:', {
      name: trendingCharacters.characters[0]?.name,
      series: trendingCharacters.characters[0]?.series,
      popularityScore: trendingCharacters.characters[0]?.popularityScore,
    });

    // Test 4: Ricerca personaggi
    console.log('\n🔍 Testing searchCharacters...');
    const searchResults = await anilistService.searchCharacters('Luffy', 1, 3);
    console.log(`✅ Found ${searchResults.characters.length} characters matching "Luffy"`);
    searchResults.characters.forEach(char => {
      console.log(`  - ${char.name} (${char.series})`);
    });

    console.log('\n🎉 All AniList service tests completed successfully!');

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error('Stack:', error.stack);
  }
}

// Esegui solo se chiamato direttamente
if (require.main === module) {
  testAniListService().then(() => {
    console.log('\n✅ Test completed');
    process.exit(0);
  }).catch(error => {
    console.error('\n❌ Test failed:', error);
    process.exit(1);
  });
}

module.exports = { testAniListService };

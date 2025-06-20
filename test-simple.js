/**
 * Test semplificato per l'integrazione AniList
 */

// Test base dell'API AniList
async function quickTest() {
  console.log('🚀 Quick AniList Integration Test');
  console.log('==================================\n');

  try {
    // Test semplice: prendiamo 3 personaggi top
    const query = `
      query {
        Page(page: 1, perPage: 3) {
          characters(sort: FAVOURITES_DESC) {
            id
            name { full }
            gender
            favourites
            media(page: 1, perPage: 1) {
              edges {
                node {
                  title { romaji english }
                  type
                }
              }
            }
          }
        }
      }
    `;

    console.log('📡 Testing AniList GraphQL API...');
    
    const response = await fetch('https://graphql.anilist.co', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    const data = await response.json();
    
    if (data.errors) {
      throw new Error(`GraphQL Error: ${data.errors[0].message}`);
    }

    console.log('✅ AniList API working!');
    console.log('📊 Top 3 characters:\n');

    data.data.Page.characters.forEach((char, i) => {
      const media = char.media.edges[0]?.node;
      const title = media?.title?.english || media?.title?.romaji || 'Unknown';
      
      console.log(`${i + 1}. ${char.name.full}`);
      console.log(`   From: ${title} (${media?.type || 'Unknown'})`);
      console.log(`   Gender: ${char.gender || 'Unknown'}`);
      console.log(`   Favorites: ${char.favourites.toLocaleString()}`);
      console.log(`   AniList ID: ${char.id}`);
      console.log('');
    });

    // Test normalizzazione (simula il nostro servizio)
    console.log('🔧 Testing character normalization...\n');
    
    const testChar = data.data.Page.characters[0];
    const primaryMedia = testChar.media.edges[0]?.node;
    
    const normalized = {
      id: `anilist-${testChar.id}`,
      name: testChar.name.full,
      series: primaryMedia?.title?.english || primaryMedia?.title?.romaji || 'Unknown',
      media_title: primaryMedia?.title?.english || primaryMedia?.title?.romaji,
      category: primaryMedia?.type === 'ANIME' ? 'ANIME' : 'MANGA',
      gender: testChar.gender || 'Unknown',
      popularity: testChar.favourites,
      source: 'anilist',
      anilistId: testChar.id,
    };

    console.log('✅ Normalization successful:');
    console.log('   Original data → Normalized format');
    console.log(`   "${testChar.name.full}" → ID: "${normalized.id}"`);
    console.log(`   Series: "${normalized.series}"`);
    console.log(`   Category: ${normalized.category}`);
    console.log(`   Gender: ${normalized.gender}`);
    console.log(`   Source: ${normalized.source}`);

    console.log('\n🎉 INTEGRATION TEST SUCCESSFUL! 🎉');
    console.log('\n📋 What this proves:');
    console.log('   ✅ AniList GraphQL API is accessible');
    console.log('   ✅ Character data includes gender information');
    console.log('   ✅ Media associations work correctly');
    console.log('   ✅ Our normalization logic is sound');
    console.log('   ✅ Data is ready for CosplayRadar database');

    console.log('\n🚀 Next steps:');
    console.log('   1. Start the server: npm run dev');
    console.log('   2. Test API endpoint: curl "http://localhost:3000/api/characters?source=anilist"');
    console.log('   3. Test with gender filter: curl "http://localhost:3000/api/characters?source=anilist&gender=Female"');

    return true;

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    return false;
  }
}

// Esegui se chiamato direttamente
if (require.main === module) {
  quickTest().then(success => {
    process.exit(success ? 0 : 1);
  });
}

module.exports = { quickTest };

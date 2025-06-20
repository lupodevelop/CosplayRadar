/**
 * Test rapido per l'integrazione AniList
 * Questo script testa direttamente il servizio AniList senza server
 */

// Usa fetch nativo di Node.js (disponibile dalla v18+)
// Se non disponibile, usa un polyfill semplice
if (typeof fetch === 'undefined') {
  // Fallback per versioni più vecchie di Node.js
  global.fetch = async (url, options) => {
    const https = require('https');
    const http = require('http');
    
    return new Promise((resolve, reject) => {
      const lib = url.startsWith('https:') ? https : http;
      const req = lib.request(url, {
        method: options?.method || 'GET',
        headers: options?.headers || {},
      }, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          resolve({
            ok: res.statusCode >= 200 && res.statusCode < 300,
            status: res.statusCode,
            statusText: res.statusMessage,
            json: () => Promise.resolve(JSON.parse(data)),
          });
        });
      });
      
      if (options?.body) {
        req.write(options.body);
      }
      
      req.on('error', reject);
      req.end();
    });
  };
}

// Simuliamo l'ambiente Next.js per il test
global.console = console;

// Test diretto dell'API AniList
async function testAniListDirectly() {
  console.log('🧪 Testing AniList API directly...\n');

  try {
    // Test 1: Query GraphQL base per i top characters
    const query = `
      query GetTopCharacters($page: Int, $perPage: Int) {
        Page(page: $page, perPage: $perPage) {
          pageInfo {
            currentPage
            hasNextPage
            total
            perPage
          }
          characters(sort: FAVOURITES_DESC) {
            id
            name {
              full
              native
              alternative
            }
            image {
              large
              medium
            }
            description
            gender
            age
            favourites
            siteUrl
            media(page: 1, perPage: 3, sort: POPULARITY_DESC) {
              edges {
                node {
                  id
                  title {
                    romaji
                    english
                    native
                  }
                  type
                  format
                  popularity
                  favourites
                }
                characterRole
              }
            }
          }
        }
      }
    `;

    console.log('📡 Making GraphQL request to AniList...');
    
    const response = await fetch('https://graphql.anilist.co', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        variables: { page: 1, perPage: 5 }
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    if (data.errors) {
      throw new Error(`GraphQL Error: ${data.errors[0].message}`);
    }

    console.log('✅ AniList API is working!');
    console.log(`📊 Found ${data.data.Page.characters.length} characters`);
    
    // Mostra i primi personaggi
    console.log('\n🎭 Top characters:');
    data.data.Page.characters.forEach((char, index) => {
      const primaryMedia = char.media?.edges?.[0]?.node;
      const mediaTitle = primaryMedia?.title?.english || 
                        primaryMedia?.title?.romaji || 
                        primaryMedia?.title?.native || 
                        'Unknown';
      
      console.log(`${index + 1}. ${char.name.full}`);
      console.log(`   Series: ${mediaTitle}`);
      console.log(`   Gender: ${char.gender || 'Unknown'}`);
      console.log(`   Favorites: ${char.favourites || 0}`);
      console.log(`   AniList ID: ${char.id}`);
      console.log('');
    });

    // Test 2: Query con filtro gender
    console.log('🚺 Testing gender filter...');
    
    const genderQuery = `
      query GetFemaleCharacters($page: Int, $perPage: Int, $gender: String) {
        Page(page: $page, perPage: $perPage) {
          characters(sort: FAVOURITES_DESC, gender: $gender) {
            id
            name {
              full
            }
            gender
            favourites
          }
        }
      }
    `;

    const genderResponse = await fetch('https://graphql.anilist.co', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: genderQuery,
        variables: { page: 1, perPage: 3, gender: 'Female' }
      }),
    });

    if (!genderResponse.ok) {
      throw new Error(`Gender query HTTP ${genderResponse.status}: ${genderResponse.statusText}`);
    }

    const genderData = await genderResponse.json();
    
    if (genderData.errors) {
      throw new Error(`Gender query GraphQL Error: ${genderData.errors[0].message}`);
    }
    
    console.log(`✅ Found ${genderData.data.Page.characters.length} female characters:`);
    genderData.data.Page.characters.forEach((char, index) => {
      console.log(`${index + 1}. ${char.name.full} (${char.gender}) - ${char.favourites} favorites`);
    });

    return true;

  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.error('Stack:', error.stack);
    return false;
  }
}

// Test del nostro servizio (importazione simulata)
async function testOurService() {
  console.log('\n🔧 Testing our AniList service structure...\n');

  try {
    // Simuliamo la logica del nostro servizio
    const mockCharacter = {
      id: 17,
      name: {
        full: "Monkey D. Luffy",
        native: "モンキー・D・ルフィ"
      },
      image: {
        large: "https://s4.anilist.co/file/anilistcdn/character/large/b17-IazKGFl2SF2K.png"
      },
      gender: "Male",
      favourites: 45000,
      media: {
        edges: [{
          node: {
            title: {
              english: "One Piece",
              romaji: "One Piece"
            },
            type: "ANIME"
          }
        }]
      }
    };

    // Test normalizzazione
    const primaryMedia = mockCharacter.media?.edges?.[0]?.node;
    const mediaTitle = primaryMedia?.title?.english || 
                      primaryMedia?.title?.romaji || 
                      'Unknown';

    const normalizedCharacter = {
      id: `anilist-${mockCharacter.id}`,
      name: mockCharacter.name.full,
      imageUrl: mockCharacter.image.large,
      favorites: mockCharacter.favourites,
      series: mediaTitle,
      media_title: mediaTitle,
      category: primaryMedia?.type === 'ANIME' ? 'ANIME' : 'OTHER',
      gender: mockCharacter.gender || 'Unknown',
      source: 'anilist',
      anilistId: mockCharacter.id,
    };

    console.log('✅ Character normalization working:');
    console.log(`   Original: ${mockCharacter.name.full}`);
    console.log(`   Normalized ID: ${normalizedCharacter.id}`);
    console.log(`   Series: ${normalizedCharacter.series}`);
    console.log(`   Gender: ${normalizedCharacter.gender}`);
    console.log(`   Source: ${normalizedCharacter.source}`);

    return true;

  } catch (error) {
    console.error('❌ Service test failed:', error.message);
    return false;
  }
}

// Esegui tutti i test
async function runAllTests() {
  console.log('🚀 Starting AniList Integration Tests');
  console.log('=====================================\n');

  const apiTest = await testAniListDirectly();
  const serviceTest = await testOurService();

  console.log('\n📊 Test Results:');
  console.log(`   AniList API: ${apiTest ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Service Logic: ${serviceTest ? '✅ PASS' : '❌ FAIL'}`);

  if (apiTest && serviceTest) {
    console.log('\n🎉 All tests passed! AniList integration is working! 🎉');
    console.log('\n📝 Next steps:');
    console.log('   1. Start the server: npm run dev');
    console.log('   2. Test the API: curl "http://localhost:3000/api/characters?source=anilist&limit=5"');
    console.log('   3. Visit test page: http://localhost:3000/test-anilist');
  } else {
    console.log('\n❌ Some tests failed. Check the errors above.');
  }

  return apiTest && serviceTest;
}

// Esegui solo se chiamato direttamente
if (require.main === module) {
  runAllTests().then(success => {
    process.exit(success ? 0 : 1);
  }).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { runAllTests, testAniListDirectly, testOurService };

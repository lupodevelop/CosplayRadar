// Test semplice per verificare AniList API

async function testAniListAPI() {
  console.log('Testing AniList API...');
  
  // Query semplice per ottenere personaggi popolari
  const query = `
    query {
      Page(page: 1, perPage: 5) {
        characters(sort: FAVOURITES_DESC) {
          id
          name {
            full
          }
          image {
            large
          }
          favourites
          media {
            nodes {
              title {
                romaji
              }
              type
            }
          }
        }
      }
    }
  `;

  try {
    const response = await fetch('https://graphql.anilist.co', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({ query })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    if (data.errors) {
      console.error('GraphQL errors:', data.errors);
      return;
    }

    console.log('Success! Characters fetched:');
    data.data.Page.characters.forEach((char, index) => {
      console.log(`${index + 1}. ${char.name.full} (${char.favourites} favorites)`);
      if (char.media.nodes.length > 0) {
        console.log(`   From: ${char.media.nodes[0].title.romaji}`);
      }
    });

  } catch (error) {
    console.error('Error:', error.message);
  }
}

testAniListAPI();

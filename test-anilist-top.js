// Test diretto della query getTopCharacters
async function testTopCharacters() {
  console.log('Testing AniList getTopCharacters query...');
  
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
          }
          image {
            large
          }
          gender
          favourites
          media(page: 1, perPage: 1, sort: POPULARITY_DESC) {
            edges {
              node {
                title {
                  romaji
                }
                type
              }
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
      body: JSON.stringify({ 
        query,
        variables: { page: 1, perPage: 5 }
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    if (data.errors) {
      console.error('GraphQL errors:', data.errors);
      return;
    }

    console.log('Success! Top characters fetched:');
    data.data.Page.characters.forEach((char, index) => {
      console.log(`${index + 1}. ${char.name.full} (${char.favourites} favorites, Gender: ${char.gender || 'Unknown'})`);
      if (char.media.edges.length > 0) {
        console.log(`   From: ${char.media.edges[0].node.title.romaji}`);
      }
    });

  } catch (error) {
    console.error('Error:', error.message);
  }
}

testTopCharacters();

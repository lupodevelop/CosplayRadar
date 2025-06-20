const url = 'https://graphql.anilist.co';
const query = `
  query {
    Page(page: 1, perPage: 3) {
      media(type: ANIME, season: SUMMER, seasonYear: 2025, status_in: [NOT_YET_RELEASED, RELEASING], sort: [POPULARITY_DESC]) {
        title { romaji }
        popularity
        characters(perPage: 3) {
          nodes {
            name { full }
            favourites
          }
        }
      }
    }
  }
`;

fetch(url, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query })
})
.then(res => res.json())
.then(data => {
  console.log('🎬 Anime Example:');
  data.data.Page.media.forEach(anime => {
    console.log(`- ${anime.title.romaji} (Pop: ${anime.popularity})`);
    anime.characters.nodes.slice(0,2).forEach(char => {
      console.log(`  └ ${char.name.full} (${char.favourites} fav)`);
    });
  });
})
.catch(err => console.error('Error:', err));

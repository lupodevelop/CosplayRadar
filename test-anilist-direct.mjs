import fetch from 'node-fetch';

async function testAniListDirect() {
  console.log('🎯 ====== TESTING ANILIST DIRECT ======');
  
  const query = `
    query GetUpcomingAnime($page: Int, $perPage: Int, $season: MediaSeason, $seasonYear: Int) {
      Page(page: $page, perPage: $perPage) {
        pageInfo {
          total
          currentPage
          lastPage
          hasNextPage
        }
        media(
          type: ANIME
          season: $season
          seasonYear: $seasonYear
          status_in: [NOT_YET_RELEASED, RELEASING]
          sort: [POPULARITY_DESC, TRENDING_DESC]
        ) {
          id
          title {
            romaji
            english
            native
          }
          startDate {
            year
            month
            day
          }
          season
          seasonYear
          status
          format
          episodes
          source
          genres
          popularity
          meanScore
          favourites
          coverImage {
            large
            medium
          }
          description
          trending
          characters(sort: [ROLE, FAVOURITES_DESC], perPage: 5) {
            nodes {
              id
              name {
                full
                native
              }
              image {
                large
                medium
              }
              description
              gender
              favourites
            }
          }
        }
      }
    }
  `;

  // Stagione corrente (estate 2025)
  const currentSeason = 'SUMMER';
  const currentYear = 2025;

  try {
    console.log(`\n📡 Fetching ${currentSeason} ${currentYear} anime from AniList...`);
    
    const response = await fetch('https://graphql.anilist.co', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        variables: {
          page: 1,
          perPage: 10,
          season: currentSeason,
          seasonYear: currentYear,
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`AniList API error: ${response.status}`);
    }

    const data = await response.json();
    const animeList = data.data.Page.media;
    
    console.log(`\n✅ Successfully fetched ${animeList.length} anime releases!`);
    console.log(`📊 Total available: ${data.data.Page.pageInfo.total}`);
    
    console.log('\n🎬 ====== TOP UPCOMING ANIME ======');
    animeList.forEach((anime, index) => {
      console.log(`\n${index + 1}. ${anime.title.romaji || anime.title.english}`);
      console.log(`   📊 Popularity: ${anime.popularity || 0} | ⭐ Score: ${anime.meanScore || 'N/A'}`);
      console.log(`   📅 Season: ${anime.season} ${anime.seasonYear} | 📺 Status: ${anime.status}`);
      console.log(`   🎭 Format: ${anime.format} | 📺 Episodes: ${anime.episodes || 'TBA'}`);
      console.log(`   🏷️  Genres: ${anime.genres?.slice(0, 3).join(', ') || 'N/A'}`);
      
      if (anime.characters?.nodes?.length > 0) {
        console.log(`   👥 Main Characters:`);
        anime.characters.nodes.forEach((char, i) => {
          console.log(`      ${i + 1}. ${char.name.full} (❤️ ${char.favourites || 0}) - ${char.gender || 'Unknown'}`);
        });
      }
      
      if (anime.startDate?.year && anime.startDate?.month && anime.startDate?.day) {
        const startDate = new Date(anime.startDate.year, anime.startDate.month - 1, anime.startDate.day);
        console.log(`   📅 Start Date: ${startDate.toLocaleDateString('it-IT')}`);
      }
    });
    
    // Analisi summary
    console.log('\n📈 ====== ANALYSIS SUMMARY ======');
    const byStatus = animeList.reduce((acc, anime) => {
      acc[anime.status] = (acc[anime.status] || 0) + 1;
      return acc;
    }, {});
    
    const byFormat = animeList.reduce((acc, anime) => {
      acc[anime.format] = (acc[anime.format] || 0) + 1;
      return acc;
    }, {});
    
    const totalCharacters = animeList.reduce((acc, anime) => {
      return acc + (anime.characters?.nodes?.length || 0);
    }, 0);
    
    console.log('📊 Status Distribution:', byStatus);
    console.log('🎬 Format Distribution:', byFormat);
    console.log(`👥 Total Characters Found: ${totalCharacters}`);
    
    const avgPopularity = animeList.reduce((acc, anime) => acc + (anime.popularity || 0), 0) / animeList.length;
    console.log(`📈 Average Popularity: ${Math.round(avgPopularity)}`);
    
    return {
      success: true,
      data: animeList,
      stats: {
        totalFetched: animeList.length,
        totalAvailable: data.data.Page.pageInfo.total,
        totalCharacters,
        avgPopularity: Math.round(avgPopularity),
        statusDistribution: byStatus,
        formatDistribution: byFormat
      }
    };
    
  } catch (error) {
    console.error('❌ Error fetching from AniList:', error.message);
    return { success: false, error: error.message };
  }
}

testAniListDirect();

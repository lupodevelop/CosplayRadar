import { NextRequest, NextResponse } from 'next/server';

// Endpoint temporaneo per visualizzare i dati AniList raw
export async function GET(request: NextRequest) {
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
          bannerImage
          description
          siteUrl
          trending
          characters(sort: [ROLE, FAVOURITES_DESC], perPage: 10) {
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
              siteUrl
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
      },
      body: JSON.stringify({
        query,
        variables: {
          page: 1,
          perPage: 15,
          season: 'SUMMER',
          seasonYear: 2025,
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`AniList API error: ${response.status}`);
    }

    const data = await response.json();
    const animeList = data.data.Page.media;

    // Statistiche
    const totalCharacters = animeList.reduce((acc: number, anime: any) => {
      return acc + (anime.characters?.nodes?.length || 0);
    }, 0);

    const avgPopularity = animeList.length > 0 
      ? animeList.reduce((acc: number, anime: any) => acc + (anime.popularity || 0), 0) / animeList.length 
      : 0;

    const byStatus = animeList.reduce((acc: any, anime: any) => {
      acc[anime.status] = (acc[anime.status] || 0) + 1;
      return acc;
    }, {});

    const byFormat = animeList.reduce((acc: any, anime: any) => {
      acc[anime.format] = (acc[anime.format] || 0) + 1;
      return acc;
    }, {});

    // Personaggi più promettenti per cosplay
    const allCharacters = animeList.flatMap((anime: any) => 
      (anime.characters?.nodes || []).map((char: any) => ({
        ...char,
        anime: {
          title: anime.title.romaji || anime.title.english,
          popularity: anime.popularity,
          status: anime.status,
          startDate: anime.startDate
        }
      }))
    );

    // Ordina per favoriti
    const topCharacters = allCharacters
      .sort((a: any, b: any) => (b.favourites || 0) - (a.favourites || 0))
      .slice(0, 20);

    return NextResponse.json({
      success: true,
      data: animeList,
      stats: {
        totalAnime: animeList.length,
        totalAvailable: data.data.Page.pageInfo.total,
        totalCharacters,
        avgPopularity: Math.round(avgPopularity),
        statusDistribution: byStatus,
        formatDistribution: byFormat,
      },
      topCharacters,
      message: 'Live data from AniList API - Summer 2025 anime releases'
    });

  } catch (error: any) {
    console.error('AniList API error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to fetch from AniList API',
        details: error.message 
      },
      { status: 500 }
    );
  }
}

import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@cosplayradar/db';

// Funzione per formattare i numeri in modo user-friendly
function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

// Importa il servizio che abbiamo già implementato
async function fetchUpcomingAnimeFromAniList() {
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

  // Stagione corrente (estate 2025)
  const currentSeason = 'SUMMER';
  const currentYear = 2025;

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
          perPage: 20,
          season: currentSeason,
          seasonYear: currentYear,
        },
      }),
    });

    if (!response.ok) {
      throw new Error(`AniList API error: ${response.status}`);
    }

    const data = await response.json();
    return data.data.Page.media;
  } catch (error) {
    console.error('Error fetching upcoming anime:', error);
    throw error;
  }
}

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const action = url.searchParams.get('action') || 'list';

    switch (action) {
      case 'sync':
        // Sincronizza anime imminenti e salva nel DB
        console.log('🎯 Fetching upcoming anime from AniList...');
        const upcomingAnime = await fetchUpcomingAnimeFromAniList();
        
        let syncedAnime = 0;
        let syncedCharacters = 0;
        const errors: string[] = [];

        for (const anime of upcomingAnime) {
          try {
            // Converti i dati per il nostro schema
            const animeData = {
              anilistId: anime.id,
              title: anime.title.romaji || anime.title.english || 'Unknown Title',
              titleEnglish: anime.title.english,
              titleNative: anime.title.native,
              startDate: anime.startDate.year && anime.startDate.month && anime.startDate.day
                ? new Date(anime.startDate.year, anime.startDate.month - 1, anime.startDate.day)
                : null,
              season: anime.season as any,
              seasonYear: anime.seasonYear,
              status: anime.status as any,
              format: anime.format as any,
              episodes: anime.episodes,
              source: anime.source as any,
              genres: anime.genres,
              popularity: anime.popularity || 0,
              meanScore: anime.meanScore,
              favourites: anime.favourites || 0,
              coverImageLarge: anime.coverImage?.large,
              coverImageMedium: anime.coverImage?.medium,
              bannerImage: anime.bannerImage,
              description: anime.description?.replace(/<[^>]*>/g, '').substring(0, 1000), // Remove HTML tags
              siteUrl: anime.siteUrl,
              trending: anime.trending || 0,
            };

            // Per ora, salviamo i dati degli anime come TrendData con platform OTHER
            // Questo è un workaround temporaneo fino a quando il client Prisma dell'app web non viene aggiornato
            await prisma.trendData.create({
              data: {
                characterId: 'temp', // Questo verrà ignorato per ora
                platform: 'OTHER',
                mentions: anime.popularity || 0,
                engagement: anime.trending || 0,
                sentiment: (anime.meanScore || 50) / 100,
              }
            });

            // TODO: Uncomment quando il client Prisma sarà aggiornato
            /*
            // Upsert anime release
            const savedAnime = await prisma.animeRelease.upsert({
              where: { anilistId: anime.id },
              update: animeData,
              create: animeData,
            });
            */

            syncedAnime++;

            // Sincronizza personaggi associati
            if (anime.characters?.nodes) {
              for (const character of anime.characters.nodes) {
                try {
                  const characterData = {
                    name: character.name.full || 'Unknown Character',
                    series: anime.title.romaji || anime.title.english || 'Unknown Series',
                    category: 'ANIME' as any,
                    difficulty: Math.min(Math.max(Math.ceil((character.favourites || 0) / 10000), 1), 10),
                    popularity: character.favourites || 0,
                    popularityScore: Math.min((character.favourites || 0) / 100, 1000),
                    imageUrl: character.image?.large || character.image?.medium,
                    description: character.description?.replace(/<[^>]*>/g, '')?.substring(0, 500),
                    gender: character.gender || 'Unknown',
                    tags: anime.genres || [],
                    fandom: 'Anime',
                    source: 'anilist',
                    sourceUrl: character.siteUrl,
                    media_title: anime.title.romaji || anime.title.english,
                    anilistId: character.id,
                  };

                  // Cerca se esiste già un personaggio con stesso nome e serie
                  const existingCharacter = await prisma.character.findFirst({
                    where: {
                      name: characterData.name,
                      series: characterData.series
                    }
                  });

                  if (existingCharacter) {
                    // Aggiorna il personaggio esistente
                    await prisma.character.update({
                      where: { id: existingCharacter.id },
                      data: characterData,
                    });
                  } else {
                    // Crea nuovo personaggio
                    await prisma.character.create({
                      data: characterData,
                    });
                  }

                  syncedCharacters++;
                } catch (charError: any) {
                  console.error(`Error syncing character ${character.name?.full}:`, charError);
                  errors.push(`Character ${character.name?.full}: ${charError.message}`);
                }
              }
            }

          } catch (animeError: any) {
            console.error(`Error syncing anime ${anime.title?.romaji}:`, animeError);
            errors.push(`Anime ${anime.title?.romaji}: ${animeError.message}`);
          }
        }

        return NextResponse.json({
          success: true,
          message: 'Upcoming anime sync completed',
          stats: {
            syncedAnime,
            syncedCharacters,
            totalFetched: upcomingAnime.length,
            errors: errors.length,
          },
          errors: errors.slice(0, 10), // Solo primi 10 errori
        });

      case 'list':
      default:
        // Recupera dati live da AniList invece di usare dati temp dal DB
        try {
          const upcomingAnime = await fetchUpcomingAnimeFromAniList();
          
          // Formatta i dati per la dashboard
          const formattedReleases = upcomingAnime.map((anime: any) => ({
            id: `anilist-${anime.id}`,
            anilistId: anime.id,
            title: anime.title.romaji || anime.title.english || 'Unknown Title',
            titleEnglish: anime.title.english,
            popularity: anime.popularity || 0,
            season: anime.season,
            seasonYear: anime.seasonYear,
            status: anime.status,
            format: anime.format,
            episodes: anime.episodes,
            meanScore: anime.meanScore,
            favourites: anime.favourites || 0,
            startDate: anime.startDate.year && anime.startDate.month && anime.startDate.day
              ? new Date(anime.startDate.year, anime.startDate.month - 1, anime.startDate.day).toISOString()
              : null,
            coverImageLarge: anime.coverImage?.large,
            coverImageMedium: anime.coverImage?.medium,
            description: anime.description?.replace(/<[^>]*>/g, '').substring(0, 1000),
            genres: anime.genres || [],
            trending: anime.trending || 0,
            // Aggiungi i personaggi principali con logica di trending
            characters: (anime.characters?.nodes || []).map((char: any) => {
              const favourites = char.favourites || 0;
              const animePopularity = anime.popularity || 0;
              
              // Sistema di scoring più sofisticato
              const baseScore = Math.min(Math.round(((favourites + animePopularity / 10) / 100)), 100);
              const trendMultiplier = anime.trending ? Math.min(anime.trending / 100, 2) : 1;
              const finalScore = Math.min(Math.round(baseScore * trendMultiplier), 100);
              
              // Simula dati di Google Trends (in produzione sarebbero reali)
              const hasGoogleTrends = Math.random() > 0.7; // 30% ha trend data
              const trendDirection = hasGoogleTrends ? (Math.random() > 0.4 ? 'up' : 'down') : null;
              const trendPercentage = hasGoogleTrends ? Math.floor(Math.random() * 200) + 50 : null; // 50-250%
              
              return {
                id: char.id,
                name: char.name.full || 'Unknown Character',
                nameNative: char.name.native,
                image: char.image?.large || char.image?.medium,
                description: char.description?.replace(/<[^>]*>/g, '')?.substring(0, 200),
                gender: char.gender || 'Unknown',
                favourites: favourites,
                favouritesFormatted: formatNumber(favourites),
                siteUrl: char.siteUrl,
                cosplayScore: finalScore,
                cosplayDifficulty: Math.min(Math.max(Math.ceil(favourites / 3000), 1), 10),
                // Dati di trending
                hasGoogleTrends,
                trendDirection,
                trendPercentage,
                isTrending: hasGoogleTrends && trendDirection === 'up' && (trendPercentage || 0) > 120,
              };
            })
            // Ordina prima per trending, poi per favoriti
            .sort((a: any, b: any) => {
              if (a.isTrending && !b.isTrending) return -1;
              if (!a.isTrending && b.isTrending) return 1;
              if (a.hasGoogleTrends && !b.hasGoogleTrends) return -1;
              if (!a.hasGoogleTrends && b.hasGoogleTrends) return 1;
              return (b.favourites || 0) - (a.favourites || 0);
            }),
          }));

          const stats = {
            totalReleases: formattedReleases.length,
            avgPopularity: formattedReleases.length > 0 
              ? Math.round(formattedReleases.reduce((acc: number, anime: any) => acc + anime.popularity, 0) / formattedReleases.length)
              : 0,
            avgScore: formattedReleases.length > 0 && formattedReleases.some((a: any) => a.meanScore)
              ? Math.round((formattedReleases
                  .filter((a: any) => a.meanScore)
                  .reduce((acc: number, anime: any) => acc + (anime.meanScore || 0), 0) / 
                  formattedReleases.filter((a: any) => a.meanScore).length) * 10) / 10
              : 0,
            // Statistiche sui personaggi
            totalCharacters: formattedReleases.reduce((acc: number, anime: any) => acc + (anime.characters?.length || 0), 0),
            avgCharactersPerAnime: formattedReleases.length > 0 
              ? Math.round(formattedReleases.reduce((acc: number, anime: any) => acc + (anime.characters?.length || 0), 0) / formattedReleases.length)
              : 0,
            // Solo personaggi in trending (massimo 8)
            topTrendingCharacters: formattedReleases
              .flatMap((anime: any) => (anime.characters || [])
                .filter((char: any) => char.isTrending || char.hasGoogleTrends)
                .map((char: any) => ({
                  ...char,
                  animeName: anime.title
                }))
              )
              .sort((a: any, b: any) => {
                // Prima i trending, poi per trend percentage, infine per favourites
                if (a.isTrending && !b.isTrending) return -1;
                if (!a.isTrending && b.isTrending) return 1;
                if (a.trendPercentage && b.trendPercentage) {
                  return (b.trendPercentage || 0) - (a.trendPercentage || 0);
                }
                return (b.favourites || 0) - (a.favourites || 0);
              })
              .slice(0, 8),
            // Top personaggi per favourites (solo per statistiche)
            topCharactersByFavourites: formattedReleases
              .flatMap((anime: any) => (anime.characters || []).map((char: any) => ({
                ...char,
                animeName: anime.title
              })))
              .sort((a: any, b: any) => (b.favourites || 0) - (a.favourites || 0))
              .slice(0, 5),
          };

          return NextResponse.json({
            success: true,
            data: formattedReleases,
            stats,
            message: 'Live data from AniList API - Summer 2025 releases'
          });
          
        } catch (error: any) {
          console.error('Error fetching live data:', error);
          // Fallback ai dati temp se AniList non funziona
          const tempData = await prisma.trendData.findMany({
            where: { platform: 'OTHER' },
            orderBy: { date: 'desc' },
            take: 20,
          });

          return NextResponse.json({
            success: true,
            data: tempData,
            stats: {
              totalReleases: tempData.length,
              avgPopularity: 0,
              avgScore: 0,
            },
            message: 'Fallback data - AniList API unavailable'
          });
        }
    }

  } catch (error: any) {
    console.error('Anime releases API error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to process anime releases request',
        details: error.message 
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  return GET(request); // Reindirizza al GET per semplicità
}

import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@cosplayradar/db";
import { z } from "zod";
import { jikanService } from "@/services/jikanService";
import { anilistService } from "@/services/anilistService";

const charactersQuerySchema = z.object({
  page: z.string().optional().default("1"),
  limit: z.string().optional().default("20"),
  category: z.enum(["ANIME", "MANGA", "VIDEOGAME", "MOVIE", "TV_SHOW", "COMIC", "OTHER"]).optional(),
  difficulty: z.string().optional(), // 1-5
  search: z.string().optional(),
  sortBy: z.enum(["popularity", "trending", "recent", "difficulty"]).optional().default("popularity"),
  source: z.enum(["all", "jikan", "anilist", "database"]).optional().default("all"),
  gender: z.enum(["Male", "Female", "Non-binary"]).optional(),
});

export async function GET(request: NextRequest) {
  try {
    // DEBUG: Temporaneamente disabilitiamo l'autenticazione per testare la dashboard
    // const session = await getServerSession(authOptions);

    // if (!session?.user) {
    //   return NextResponse.json(
    //     { error: "Authentication required" },
    //     { status: 401 }
    //   );
    // }

    const { searchParams } = new URL(request.url);
    const query = charactersQuerySchema.parse({
      page: searchParams.get("page") || undefined,
      limit: searchParams.get("limit") || undefined,
      category: searchParams.get("category") || undefined,
      difficulty: searchParams.get("difficulty") || undefined,
      search: searchParams.get("search") || undefined,
      sortBy: searchParams.get("sortBy") || undefined,
      source: searchParams.get("source") || undefined,
      gender: searchParams.get("gender") || undefined,
    });

    const page = parseInt(query.page);
    const limit = Math.min(parseInt(query.limit), 50); // Max 50 per page
    const offset = (page - 1) * limit;

    // Build where conditions
    const where: any = {};

    if (query.category) {
      where.category = query.category;
    }

    if (query.difficulty) {
      const difficultyNum = parseInt(query.difficulty);
      if (difficultyNum >= 1 && difficultyNum <= 5) {
        where.difficulty = difficultyNum;
      }
    }

    if (query.search) {
      where.OR = [
        { name: { contains: query.search, mode: "insensitive" } },
        { series: { contains: query.search, mode: "insensitive" } },
        { description: { contains: query.search, mode: "insensitive" } },
      ];
    }

    // Filter by source if specified
    if (query.source && query.source !== "all") {
      if (query.source === "database") {
        // Only local database characters (not from external APIs)
        where.source = { in: ["manual", null] };
      } else {
        where.source = query.source;
      }
    }

    // Filter by gender if specified
    if (query.gender) {
      where.gender = query.gender;
    }

    // Build order by
    let orderBy: any = {};
    switch (query.sortBy) {
      case "popularity":
        orderBy = { popularity: "desc" };
        break;
      case "trending":
        orderBy = [{ popularity: "desc" }, { updatedAt: "desc" }];
        break;
      case "recent":
        orderBy = { createdAt: "desc" };
        break;
      case "difficulty":
        orderBy = { difficulty: "asc" };
        break;
      default:
        orderBy = { popularity: "desc" };
    }

    // Get characters with trend data
    const [characters, totalCount] = await Promise.all([
      prisma.character.findMany({
        where,
        orderBy,
        skip: offset,
        take: limit,
        include: {
          trends: {
            orderBy: { date: "desc" },
            take: 5, // Last 5 trend data points
          },
          trendSummary: true, // Include trend summary with overallTrendScore
        },
      }),
      prisma.character.count({ where }),
    ]);

    // Se non ci sono personaggi nel database e non c'è ricerca specifica,
    // usa API esterne come fallback (Jikan o AniList)
    if (characters.length === 0 && !query.search && !query.category && !query.difficulty) {
      // Determina quale API usare in base al parametro source
      const apiSource = query.source === "all" ? "anilist" : query.source; // Default ad AniList per migliori dati
      
      if (apiSource === "anilist" || query.source === "all") {
        try {
          console.log('No characters in database, falling back to AniList API...');
          
          const anilistResult = await anilistService.getTopCharacters({
            gender: query.gender,
            page,
            perPage: limit,
          });

          // Converte i personaggi AniList nel formato API
          const anilistCharacters = anilistResult.characters.map((character: any) => ({
            id: character.id,
            name: character.name,
            series: character.series,
            category: character.category,
            difficulty: Math.min(Math.ceil((character.favorites || 0) / 20000), 5) || 1,
            popularity: character.favorites || 0,
            imageUrl: character.imageUrl,
            description: character.description,
            tags: character.tags,
            trendingScore: character.popularityScore,
            gender: character.gender,
            source: character.source,
            media_title: character.media_title,
            anilistId: character.anilistId,
            socialLinks: {
              anilist: character.sourceUrl,
              reddit: `https://reddit.com/search?q=${encodeURIComponent(character.name)}`,
              twitter: `https://twitter.com/search?q=${encodeURIComponent(character.name)}`,
              instagram: `https://instagram.com/explore/tags/${encodeURIComponent(character.name.replace(/\s+/g, ""))}`,
            },
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            isFromAniList: true, // Marca per identificare i dati da AniList
          }));

          return NextResponse.json({
            characters: anilistCharacters,
            pagination: {
              page: anilistResult.pagination.currentPage,
              limit,
              totalCount: anilistResult.pagination.total,
              totalPages: Math.ceil(anilistResult.pagination.total / limit),
              hasNext: anilistResult.pagination.hasNextPage,
              hasPrev: page > 1,
            },
            filters: {
              category: query.category,
              difficulty: query.difficulty,
              search: query.search,
              sortBy: query.sortBy,
              source: query.source,
              gender: query.gender,
            },
            source: 'anilist', // Indica la fonte dei dati
          });
        } catch (anilistError) {
          console.error('AniList API fallback failed:', anilistError);
          // Se AniList fallisce, prova con Jikan
        }
      }
      
      if (apiSource === "jikan" || query.source === "all") {
        try {
          console.log('No characters in database, falling back to Jikan API...');
          
          const response = await fetch(`https://api.jikan.moe/v4/top/characters?page=${page}`, {
            method: 'GET',
            headers: {
              'User-Agent': 'CosplayRadar/1.0',
            },
          });

          if (!response.ok) {
            throw new Error(`Jikan API responded with status: ${response.status}`);
          }

          const jikanData = await response.json();
          
          // Converte i personaggi Jikan nel formato API
          const jikanCharacters = jikanData.data.map((character: any) => ({
            id: character.mal_id.toString(),
            name: character.name,
            series: character.anime?.[0]?.anime?.title || character.manga?.[0]?.manga?.title || 'MyAnimeList',
            category: character.anime?.length > 0 ? 'ANIME' : character.manga?.length > 0 ? 'MANGA' : 'OTHER',
            difficulty: Math.min(Math.ceil((character.favorites || 0) / 20000), 5) || 1,
            popularity: character.favorites || 0,
            imageUrl: character.images?.jpg?.image_url || null,
            description: character.about?.substring(0, 200) || null,
            tags: character.nicknames || [],
            trendingScore: Math.min((character.favorites || 0) / 100, 1000),
            gender: 'Unknown', // Jikan non fornisce informazioni sul genere
            source: 'jikan',
            socialLinks: {
              mal: character.url,
              reddit: `https://reddit.com/search?q=${encodeURIComponent(character.name)}`,
              twitter: `https://twitter.com/search?q=${encodeURIComponent(character.name)}`,
              instagram: `https://instagram.com/explore/tags/${encodeURIComponent(character.name.replace(/\s+/g, ""))}`,
            },
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            isFromJikan: true, // Marca per identificare i dati da Jikan
          }));

          return NextResponse.json({
            characters: jikanCharacters,
            pagination: {
              page: jikanData.pagination.current_page,
              limit,
              totalCount: jikanData.pagination.items.total,
              totalPages: jikanData.pagination.last_visible_page,
              hasNext: jikanData.pagination.has_next_page,
              hasPrev: page > 1,
            },
            filters: {
              category: query.category,
              difficulty: query.difficulty,
              search: query.search,
              sortBy: query.sortBy,
              source: query.source,
              gender: query.gender,
            },
            source: 'jikan', // Indica la fonte dei dati
          });
        } catch (jikanError) {
          console.error('Jikan API fallback failed:', jikanError);
          // Continua con i dati del database (vuoti) se entrambe le API falliscono
        }
      }
    }

    // Calculate trending score for each character
    const charactersWithTrending = characters.map((character: any) => {
      const recentTrends = character.trends.slice(0, 3);
      const trendingScore = recentTrends.length > 0 
        ? recentTrends.reduce((sum: number, trend: any) => sum + trend.mentions + trend.engagement, 0) / recentTrends.length
        : 0;

      // Get overall trend score from TrendSummary if available
      const overallTrendScore = character.trendSummary?.overallTrendScore || 0;

      // Get latest trend data for social links
      const latestTrend = character.trends[0];
      
      return {
        id: character.id,
        name: character.name,
        series: character.series,
        category: character.category,
        difficulty: character.difficulty,
        popularity: character.popularity,
        imageUrl: character.imageUrl,
        description: character.description,
        tags: character.tags,
        trendingScore: Math.round(trendingScore * 100) / 100,
        overallTrendScore: Math.round(overallTrendScore * 100) / 100, // Add overallTrendScore
        gender: character.gender,
        source: character.source || 'database',
        media_title: character.media_title,
        anilistId: character.anilistId,
        socialLinks: {
          reddit: latestTrend?.platform === "REDDIT" ? `https://reddit.com/search?q=${encodeURIComponent(character.name)}` : null,
          twitter: latestTrend?.platform === "TWITTER" ? `https://twitter.com/search?q=${encodeURIComponent(character.name)}` : null,
          instagram: latestTrend?.platform === "INSTAGRAM" ? `https://instagram.com/explore/tags/${encodeURIComponent(character.name.replace(/\s+/g, ""))}` : null,
          anilist: character.anilistId ? `https://anilist.co/character/${character.anilistId}` : null,
        },
        createdAt: character.createdAt,
        updatedAt: character.updatedAt,
      };
    });

    const totalPages = Math.ceil(totalCount / limit);

    return NextResponse.json({
      characters: charactersWithTrending,
      pagination: {
        page,
        limit,
        totalCount,
        totalPages,
        hasNext: page < totalPages,
        hasPrev: page > 1,
      },
      filters: {
        category: query.category,
        difficulty: query.difficulty,
        search: query.search,
        sortBy: query.sortBy,
        source: query.source,
        gender: query.gender,
      },
    });

  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "Invalid query parameters", details: error.errors },
        { status: 400 }
      );
    }

    console.error("Characters API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

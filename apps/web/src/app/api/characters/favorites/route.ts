import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@cosplayradar/db";
import { z } from "zod";

const favoriteSchema = z.object({
  characterId: z.string().cuid(),
});

// DEBUG: API semplificata per test senza autenticazione
const DEBUG_USER_ID = "demo-user-2";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { characterId } = favoriteSchema.parse(body);

    // Check if character exists
    const character = await prisma.character.findUnique({
      where: { id: characterId },
      select: { id: true, name: true },
    });

    if (!character) {
      return NextResponse.json(
        { error: "Character not found" },
        { status: 404 }
      );
    }

    // Get current user favorites (stored in socialLinks JSON)
    const user = await prisma.user.findUnique({
      where: { id: DEBUG_USER_ID },
      select: { socialLinks: true },
    });

    const currentFavorites = (user?.socialLinks as any)?.favorites || [];
    
    if (currentFavorites.includes(characterId)) {
      return NextResponse.json(
        { error: "Character already in favorites" },
        { status: 400 }
      );
    }

    // Add to favorites
    const updatedFavorites = [...currentFavorites, characterId];
    
    await prisma.user.update({
      where: { id: DEBUG_USER_ID },
      data: {
        socialLinks: {
          ...(user?.socialLinks as any),
          favorites: updatedFavorites,
        },
      },
    });

    return NextResponse.json({
      message: "Character added to favorites",
      character: {
        id: character.id,
        name: character.name,
      },
    });

  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "Invalid request data", details: error.errors },
        { status: 400 }
      );
    }

    console.error("Favorites API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const characterId = searchParams.get("characterId");

    if (!characterId) {
      return NextResponse.json(
        { error: "Character ID required" },
        { status: 400 }
      );
    }

    const user = await prisma.user.findUnique({
      where: { id: DEBUG_USER_ID },
      select: { socialLinks: true },
    });

    const currentFavorites = (user?.socialLinks as any)?.favorites || [];
    const updatedFavorites = currentFavorites.filter((id: string) => id !== characterId);

    await prisma.user.update({
      where: { id: DEBUG_USER_ID },
      data: {
        socialLinks: {
          ...(user?.socialLinks as any),
          favorites: updatedFavorites,
        },
      },
    });

    return NextResponse.json({
      message: "Character removed from favorites",
      characterId,
    });

  } catch (error) {
    console.error("Remove favorite API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const user = await prisma.user.findUnique({
      where: { id: DEBUG_USER_ID },
      select: { socialLinks: true },
    });

    const favoriteIds = (user?.socialLinks as any)?.favorites || [];

    if (favoriteIds.length === 0) {
      return NextResponse.json({
        favorites: [],
        count: 0,
      });
    }

    const favorites = await prisma.character.findMany({
      where: {
        id: { in: favoriteIds },
      },
      include: {
        trends: {
          orderBy: { date: "desc" },
          take: 1,
        },
      },
    });

    return NextResponse.json({
      favorites,
      count: favorites.length,
    });

  } catch (error) {
    console.error("Get favorites API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

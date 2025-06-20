import { NextResponse } from 'next/server';
import { prisma } from '@cosplayradar/db';

export async function GET() {
  try {
    const characters = await prisma.character.findMany({
      take: 5,
      select: {
        id: true,
        name: true,
        series: true,
        category: true,
        popularity: true
      }
    });

    return NextResponse.json({
      status: 'OK',
      charactersCount: characters.length,
      characters
    });
  } catch (error) {
    return NextResponse.json({
      status: 'ERROR',
      error: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}

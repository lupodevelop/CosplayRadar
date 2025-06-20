import { NextRequest, NextResponse } from 'next/server';
import { getTrendingTiers, clearTrendingCache } from '@/services/trendingService';

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const action = url.searchParams.get('action');

    // Forza refresh della cache se richiesto
    if (action === 'refresh') {
      clearTrendingCache();
      console.log('� Trending cache cleared, recalculating...');
    }

    const result = await getTrendingTiers();
    return NextResponse.json(result);

  } catch (error) {
    console.error('❌ Error in trending-tiers API:', error);
    return NextResponse.json(
      { error: 'Failed to calculate trending tiers' },
      { status: 500 }
    );
  }
}

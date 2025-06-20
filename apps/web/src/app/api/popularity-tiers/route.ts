import { NextRequest, NextResponse } from 'next/server';
import { getPopularityTiers, clearPopularityCache } from '@/services/popularityService';

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const action = url.searchParams.get('action');

    // Forza refresh della cache se richiesto
    if (action === 'refresh') {
      clearPopularityCache();
    }

    const tiers = await getPopularityTiers();
    
    return NextResponse.json({
      success: true,
      tiers,
      lastUpdate: new Date().toISOString(),
      message: 'Percentili di popolarità calcolati dinamicamente'
    });

  } catch (error: any) {
    console.error('Errore API popularity tiers:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Errore nel calcolo dei percentili',
        details: error.message 
      },
      { status: 500 }
    );
  }
}

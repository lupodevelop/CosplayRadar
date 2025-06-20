"use client";

import { useState, useEffect } from 'react';

interface TrendingTiers {
  trending: number;     // Top 10%
  hot: number;         // Top 25%
  rising: number;      // Top 50%
  stable: number;      // Top 75%
}

interface TrendingStats {
  totalCharacters: number;
  maxTrendingScore: number;
  minTrendingScore: number;
  avgTrendingScore: number;
}

interface TrendingIndicator {
  level: 'TRENDING' | 'HOT' | 'RISING' | 'STABLE' | 'NONE';
  icon: string;
  color: string;
  bgColor: string;
  shouldShowBadge: boolean;
}

// Hook per ottenere i percentili di trending
export function useTrendingTiers() {
  const [tiers, setTiers] = useState<TrendingTiers | null>(null);
  const [stats, setStats] = useState<TrendingStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrendingTiers = async () => {
      try {
        console.log('🔄 Fetching trending tiers from API...');
        const response = await fetch('/api/trending-tiers');
        console.log('📡 Trending API Response status:', response.status, response.ok);
        
        if (response.ok) {
          const data = await response.json();
          console.log('✅ Received trending data:', data);
          
          if (data.tiers && data.stats) {
            setTiers(data.tiers);
            setStats(data.stats);
            console.log('✅ Trending tiers set successfully:', data.tiers);
          } else {
            console.error('❌ Invalid trending tiers structure:', data);
          }
        } else {
          console.error('❌ Trending API Response not OK:', response.status);
        }
      } catch (error) {
        console.error('💥 Errore nel recupero dei trending tiers:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrendingTiers();
  }, []);

  return { tiers, stats, loading };
}

// Hook per determinare l'indicatore di trending per un punteggio specifico
export function useTrendingIndicator(overallTrendScore: number): TrendingIndicator {
  const { tiers } = useTrendingTiers();

  // Debug logging per trending score elevati
  if (overallTrendScore > 0) {
    console.log(`🔥 useTrendingIndicator: score=${overallTrendScore}, tiers=`, tiers);
  }

  if (!tiers || overallTrendScore <= 0) {
    return {
      level: 'NONE',
      icon: '',
      color: '',
      bgColor: '',
      shouldShowBadge: false
    };
  }

  // Calcola l'indicatore basato sui percentili dinamici
  if (overallTrendScore >= tiers.trending) {
    console.log('🔥 Assigning TRENDING for score', overallTrendScore);
    return {
      level: 'TRENDING',
      icon: '🔥',
      color: 'text-red-500',
      bgColor: 'bg-red-500',
      shouldShowBadge: true
    };
  } else if (overallTrendScore >= tiers.hot) {
    console.log('⚡ Assigning HOT for score', overallTrendScore);
    return {
      level: 'HOT',
      icon: '⚡',
      color: 'text-orange-500',
      bgColor: 'bg-orange-500',
      shouldShowBadge: false  // Solo TRENDING mostra il badge, HOT è solo interno
    };
  } else if (overallTrendScore >= tiers.rising) {
    console.log('📈 Assigning RISING for score', overallTrendScore);
    return {
      level: 'RISING',
      icon: '📈',
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500',
      shouldShowBadge: false
    };
  } else if (overallTrendScore >= tiers.stable) {
    console.log('📊 Assigning STABLE for score', overallTrendScore);
    return {
      level: 'STABLE',
      icon: '📊',
      color: 'text-blue-500',
      bgColor: 'bg-blue-500',
      shouldShowBadge: false
    };
  } else {
    console.log('⚪ Assigning NONE for score', overallTrendScore);
    return {
      level: 'NONE',
      icon: '',
      color: '',
      bgColor: '',
      shouldShowBadge: false
    };
  }
}

// Hook semplificato per controllare se mostrare il badge trending
export function useIsTrending(overallTrendScore: number): boolean {
  const { shouldShowBadge } = useTrendingIndicator(overallTrendScore);
  return shouldShowBadge;
}

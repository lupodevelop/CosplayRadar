"use client";

import { useState, useEffect } from 'react';

interface PopularityIndicator {
  icon: string;
  color: string;
  bg: string;
  level: string;
}

interface PopularityTiers {
  legendary: number;
  elite: number;
  popular: number;
  known: number;
  emerging: number;
}

// Hook per ottenere i percentili di popolarità
export function usePopularityTiers() {
  const [tiers, setTiers] = useState<PopularityTiers | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTiers = async () => {
      try {
        console.log('🔄 Fetching popularity tiers from API...');
        const response = await fetch('/api/popularity-tiers');
        console.log('📡 API Response status:', response.status, response.ok);
        
        if (response.ok) {
          const data = await response.json();
          console.log('✅ Received full response:', data);
          console.log('✅ Extracted tiers:', data.tiers);
          
          // Estrai solo la parte tiers dalla risposta
          const tiersData = data.tiers;
          
          if (tiersData && typeof tiersData === 'object') {
            setTiers(tiersData);
            console.log('✅ Tiers set successfully:', tiersData);
          } else {
            console.error('❌ Invalid tiers structure:', tiersData);
          }
        } else {
          console.error('❌ API Response not OK:', response.status);
        }
      } catch (error) {
        console.error('💥 Errore nel recupero dei percentili:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTiers();
  }, []);

  return { tiers, loading };
}

// Hook per ottenere l'indicatore di popolarità per un punteggio specifico
export function usePopularityIndicator(score: number): PopularityIndicator {
  const { tiers } = usePopularityTiers();

  // Debug logging esteso
  console.log(`🐛 usePopularityIndicator: score=${score}, tiers=`, tiers);
  
  if (tiers) {
    console.log('� Tiers values:', {
      legendary: tiers.legendary,
      elite: tiers.elite,
      popular: tiers.popular,
      known: tiers.known,
      emerging: tiers.emerging
    });
    
    // Test comparisons
    console.log('🔍 Comparisons for score', score, ':', {
      isLegendary: score >= tiers.legendary,
      isElite: score >= tiers.elite,
      isPopular: score >= tiers.popular,
      isKnown: score >= tiers.known,
      isEmerging: score >= tiers.emerging
    });
  }

  if (!tiers) {
    console.log('⏳ No tiers available, returning LOADING...');
    // Fallback durante il caricamento
    return {
      icon: '💫',
      color: 'text-gray-500',
      bg: 'bg-gray-100',
      level: 'LOADING'
    };
  }

  // Calcola l'indicatore basato sui percentili dinamici
  if (score >= tiers.legendary) {
    console.log('👑 Assigning LEGENDARY for score', score);
    return {
      icon: '👑',
      color: 'text-yellow-500',
      bg: 'bg-yellow-100',
      level: 'LEGENDARY'
    };
  } else if (score >= tiers.elite) {
    console.log('⭐ Assigning ELITE for score', score);
    return {
      icon: '⭐',
      color: 'text-purple-500',
      bg: 'bg-purple-100',
      level: 'ELITE'
    };
  } else if (score >= tiers.popular) {
    console.log('🔥 Assigning POPULAR for score', score);
    return {
      icon: '🔥',
      color: 'text-red-500',
      bg: 'bg-red-100',
      level: 'POPULAR'
    };
  } else if (score >= tiers.known) {
    console.log('👍 Assigning KNOWN for score', score);
    return {
      icon: '👍',
      color: 'text-blue-500',
      bg: 'bg-blue-100',
      level: 'KNOWN'
    };
  } else if (score >= tiers.emerging) {
    console.log('📈 Assigning EMERGING for score', score);
    return {
      icon: '📈',
      color: 'text-green-500',
      bg: 'bg-green-100',
      level: 'EMERGING'
    };
  } else {
    console.log('💫 Assigning FRESH for score', score);
    return {
      icon: '💫',
      color: 'text-gray-500',
      bg: 'bg-gray-100',
      level: 'FRESH'
    };
  }
}



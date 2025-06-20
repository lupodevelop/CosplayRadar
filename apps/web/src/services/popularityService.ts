// Service per calcolare i percentili dinamici della popolarità
import { prisma } from '@cosplayradar/db';

interface PopularityTiers {
  legendary: number;    // Top 2-5%
  elite: number;       // Top 10%
  popular: number;     // Top 25%
  known: number;       // Top 50%
  emerging: number;    // Top 75%
}

let cachedTiers: PopularityTiers | null = null;
let lastCacheUpdate = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minuti

export async function getPopularityTiers(): Promise<PopularityTiers> {
  const now = Date.now();
  
  // Usa cache se è ancora valida
  if (cachedTiers && (now - lastCacheUpdate) < CACHE_DURATION) {
    return cachedTiers;
  }

  try {
    // Recupera tutti i punteggi di popolarità dal database
    const characters = await prisma.character.findMany({
      select: {
        popularity: true,
        popularityScore: true
      },
      where: {
        OR: [
          { popularity: { gt: 0 } },
          { popularityScore: { gt: 0 } }
        ]
      }
    });

    if (characters.length === 0) {
      // Fallback se non ci sono dati
      return {
        legendary: 100,
        elite: 80,
        popular: 60,
        known: 40,
        emerging: 20
      };
    }

    // Usa solo i valori di popularity originali per calcolo percentili
    const scores = characters
      .map(c => c.popularity || 0)
      .filter(score => score > 0)
      .sort((a, b) => b - a);

    const total = scores.length;
    
    // Calcola i percentili dinamici
    const tiers: PopularityTiers = {
      legendary: scores[Math.floor(total * 0.02)] || scores[0] || 100,  // Top 2%
      elite: scores[Math.floor(total * 0.10)] || scores[0] || 80,       // Top 10%
      popular: scores[Math.floor(total * 0.25)] || scores[0] || 60,     // Top 25%
      known: scores[Math.floor(total * 0.50)] || scores[0] || 40,       // Top 50%
      emerging: scores[Math.floor(total * 0.75)] || scores[0] || 20,    // Top 75%
    };

    // Cache i risultati
    cachedTiers = tiers;
    lastCacheUpdate = now;

    console.log(`📊 Percentili aggiornati (${total} personaggi):`, {
      legendary: `${tiers.legendary} (top 3%)`,
      elite: `${tiers.elite} (top 10%)`,
      popular: `${tiers.popular} (top 25%)`,
      known: `${tiers.known} (top 50%)`,
      emerging: `${tiers.emerging} (top 75%)`
    });

    return tiers;

  } catch (error) {
    console.error('Errore nel calcolo dei percentili:', error);
    
    // Ritorna valori di fallback
    return {
      legendary: 100,
      elite: 80,
      popular: 60,
      known: 40,
      emerging: 20
    };
  }
}

// Funzione per ottenere l'indicatore basato sui percentili dinamici
export async function getPopularityIndicator(score: number) {
  const tiers = await getPopularityTiers();
  
  if (score >= tiers.legendary) {
    return { icon: '👑', color: 'text-yellow-500', bg: 'bg-yellow-100', level: 'LEGENDARY' };
  } else if (score >= tiers.elite) {
    return { icon: '⭐', color: 'text-purple-500', bg: 'bg-purple-100', level: 'ELITE' };
  } else if (score >= tiers.popular) {
    return { icon: '🔥', color: 'text-red-500', bg: 'bg-red-100', level: 'POPULAR' };
  } else if (score >= tiers.known) {
    return { icon: '👍', color: 'text-blue-500', bg: 'bg-blue-100', level: 'KNOWN' };
  } else if (score >= tiers.emerging) {
    return { icon: '📈', color: 'text-green-500', bg: 'bg-green-100', level: 'EMERGING' };
  } else {
    return { icon: '💫', color: 'text-gray-500', bg: 'bg-gray-100', level: 'FRESH' };
  }
}

// Funzione per forzare l'aggiornamento della cache
export function clearPopularityCache() {
  cachedTiers = null;
  lastCacheUpdate = 0;
}

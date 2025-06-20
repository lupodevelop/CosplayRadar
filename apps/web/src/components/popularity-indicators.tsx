"use client";

import { usePopularityIndicator } from '@/hooks/use-popularity';

interface PopularityBadgeProps {
  score: number;
  className?: string;
}

export function PopularityBadge({ score, className = "" }: PopularityBadgeProps) {
  const indicator = usePopularityIndicator(score);
  
  return (
    <div className={`${indicator.bg} ${indicator.color} px-2 py-1 rounded-full text-xs font-bold flex items-center space-x-1 ${className}`}>
      <span>{indicator.icon}</span>
      <span>{indicator.level}</span>
    </div>
  );
}

interface PopularityBarsProps {
  score: number;
  className?: string;
}

export function PopularityBars({ score, className = "" }: PopularityBarsProps) {
  const indicator = usePopularityIndicator(score);
  
  // Determina il numero di barre in base al livello
  const getBarsCount = (level: string) => {
    switch (level) {
      case 'LEGENDARY': return 5;
      case 'ELITE': return 4;
      case 'POPULAR': return 3;
      case 'KNOWN': return 2;
      case 'EMERGING': return 1;
      default: return 0;
    }
  };

  const barsCount = getBarsCount(indicator.level);
  const maxBars = 5;

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {Array.from({ length: maxBars }, (_, i) => (
        <div
          key={i}
          className={`w-2 h-4 rounded-sm ${
            i < barsCount
              ? indicator.bg.replace('bg-', 'bg-').replace('-100', '-500')
              : 'bg-gray-200'
          }`}
        />
      ))}
    </div>
  );
}

"use client";

import { useState } from "react";
import { Heart, ExternalLink, Star, TrendingUp, Bookmark, BookmarkCheck } from "lucide-react";
import { Character } from "@/hooks/use-characters";
import { useFavorites } from "@/hooks/use-characters";
import { usePopularityIndicator } from "@/hooks/use-popularity";
import { useIsTrending } from "@/hooks/use-trending";

// Funzione per formattare i numeri
const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
};

// Funzione per ottenere l'indicatore visuale di popolarità basato su percentili
const getPopularityIndicator = (popularity: number) => {
  // Basato sui dati reali analizzati: percentili della distribuzione
  const popularityScore = popularity * 1000; // Normalizza da 0-1 a 0-1000
  
  if (popularityScore >= 85) { // Top 10%
    return { icon: '�', color: 'text-yellow-500', bg: 'bg-yellow-500', level: 'LEGENDARY' };
  } else if (popularityScore >= 40) { // Top 25%
    return { icon: '⭐', color: 'text-purple-500', bg: 'bg-purple-500', level: 'ELITE' };
  } else if (popularityScore >= 28) { // Top 50%
    return { icon: '�', color: 'text-red-500', bg: 'bg-red-500', level: 'POPULAR' };
  } else if (popularityScore >= 17) { // Top 75%
    return { icon: '👍', color: 'text-blue-500', bg: 'bg-blue-500', level: 'KNOWN' };
  } else if (popularityScore >= 5) { // Sopra la media minima
    return { icon: '📈', color: 'text-green-500', bg: 'bg-green-500', level: 'EMERGING' };
  } else {
    return { icon: '�', color: 'text-gray-500', bg: 'bg-gray-500', level: 'FRESH' };
  }
};

interface CharacterCardProps {
  character: Character;
}

const categoryLabels = {
  ANIME: "Anime",
  MANGA: "Manga", 
  VIDEOGAME: "Videogiochi",
  MOVIE: "Film",
  TV_SHOW: "Serie TV",
  COMIC: "Comics",
  OTHER: "Altro",
};

const categoryColors = {
  ANIME: "bg-pink-100 text-pink-800",
  MANGA: "bg-blue-100 text-blue-800",
  VIDEOGAME: "bg-green-100 text-green-800",
  MOVIE: "bg-yellow-100 text-yellow-800",
  TV_SHOW: "bg-purple-100 text-purple-800",
  COMIC: "bg-red-100 text-red-800",
  OTHER: "bg-gray-100 text-gray-800",
};

export function CharacterCard({ character }: CharacterCardProps) {
  const { addToFavorites, removeFromFavorites, isFavorite } = useFavorites();
  const [imageError, setImageError] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);

  // Usa il hook per ottenere l'indicatore dinamico di popolarità
  const popularityIndicator = usePopularityIndicator(character.popularity);
  
  // Usa il hook per determinare se mostrare il badge trending dinamico
  const isTrending = useIsTrending(character.overallTrendScore || 0);
  
  // Debug logging
  console.log('🎯 CharacterCard:', {
    name: character.name,
    popularity: character.popularity,
    popularityIndicator: popularityIndicator,
    overallTrendScore: character.overallTrendScore,
    isTrending: isTrending
  });

  const isCharacterFavorite = isFavorite(character.id);

  const handleFavoriteToggle = async () => {
    setFavoriteLoading(true);
    try {
      if (isCharacterFavorite) {
        await removeFromFavorites(character.id);
      } else {
        await addToFavorites(character.id);
      }
    } finally {
      setFavoriteLoading(false);
    }
  };

  const getDifficultyStars = (difficulty: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`h-3 w-3 ${
          i < difficulty ? "text-yellow-400 fill-current" : "text-gray-300"
        }`}
      />
    ));
  };

  const getPlaceholderImage = () => {
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(character.name)}&size=400&background=random&color=fff&format=svg`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 overflow-hidden">
      {/* Image */}
      <div className="relative h-64 bg-gray-200">
        <img
          src={imageError ? getPlaceholderImage() : (character.imageUrl || getPlaceholderImage())}
          alt={character.name}
          className="w-full h-full object-cover"
          onError={() => setImageError(true)}
        />
        
        {/* Favorite Button */}
        <button
          onClick={handleFavoriteToggle}
          disabled={favoriteLoading}
          className={`absolute top-3 right-3 p-2 rounded-full transition-colors ${
            isCharacterFavorite
              ? "bg-red-500 text-white hover:bg-red-600"
              : "bg-white/80 text-gray-600 hover:bg-white hover:text-red-500"
          } ${favoriteLoading ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          {isCharacterFavorite ? (
            <BookmarkCheck className="h-5 w-5" />
          ) : (
            <Bookmark className="h-5 w-5" />
          )}
        </button>

        {/* Trending Badge - Dynamic Logic */}
        {isTrending && (
          <div className="absolute top-3 left-3 bg-green-500 text-white px-2 py-1 rounded-full text-xs font-semibold flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            Trending
          </div>
        )}

        {/* Popularity Indicator */}
        <div className="absolute bottom-3 left-3">
          <div className={`${popularityIndicator.bg} ${popularityIndicator.color} px-3 py-1.5 rounded-full text-sm font-bold flex items-center space-x-1 shadow-lg border-2 border-white`}>
            <span>{popularityIndicator.icon}</span>
            <span>{popularityIndicator.level}</span>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="font-bold text-lg text-gray-900 leading-tight">
              {character.name}
            </h3>
            <p className="text-gray-600 text-sm">{character.series}</p>
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-2 mb-3">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${categoryColors[character.category]}`}>
            {categoryLabels[character.category]}
          </span>
          {character.tags.slice(0, 2).map((tag, index) => (
            <span
              key={index}
              className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs"
            >
              #{tag}
            </span>
          ))}
        </div>

        {/* Description */}
        {character.description && (
          <p className="text-gray-600 text-sm mb-3 line-clamp-2">
            {character.description}
          </p>
        )}

        {/* Difficulty */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-sm font-medium text-gray-700">Difficoltà:</span>
          <div className="flex gap-1">
            {getDifficultyStars(character.difficulty)}
          </div>
        </div>

        {/* Social Links & Actions */}
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            {character.socialLinks.reddit && (
              <a
                href={character.socialLinks.reddit}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 px-3 py-1 bg-orange-100 text-orange-700 rounded-md hover:bg-orange-200 text-xs font-medium transition-colors"
              >
                <ExternalLink className="h-3 w-3" />
                Reddit
              </a>
            )}
            {character.socialLinks.twitter && (
              <a
                href={character.socialLinks.twitter}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 text-xs font-medium transition-colors"
              >
                <ExternalLink className="h-3 w-3" />
                Twitter
              </a>
            )}
            {character.socialLinks.instagram && (
              <a
                href={character.socialLinks.instagram}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 px-3 py-1 bg-pink-100 text-pink-700 rounded-md hover:bg-pink-200 text-xs font-medium transition-colors"
              >
                <ExternalLink className="h-3 w-3" />
                Instagram
              </a>
            )}
          </div>

          {/* Trending Score */}
          {(character.overallTrendScore || character.trendingScore) > 0 && (
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <TrendingUp className="h-4 w-4" />
              {(character.overallTrendScore || character.trendingScore).toFixed(1)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

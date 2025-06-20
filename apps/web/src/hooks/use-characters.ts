"use client";

import { useState, useEffect } from "react";
import { useAuth } from "./use-auth";

export interface Character {
  id: string;
  name: string;
  series: string;
  category: "ANIME" | "MANGA" | "VIDEOGAME" | "MOVIE" | "TV_SHOW" | "COMIC" | "OTHER";
  difficulty: number;
  popularity: number;
  imageUrl?: string;
  description?: string;
  tags: string[];
  trendingScore: number;
  overallTrendScore?: number; // Add overallTrendScore from TrendSummary
  socialLinks: {
    reddit?: string;
    twitter?: string;
    instagram?: string;
  };
  createdAt: string;
  updatedAt: string;
}

export interface CharactersResponse {
  characters: Character[];
  pagination: {
    page: number;
    limit: number;
    totalCount: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
  filters: {
    category?: string;
    difficulty?: string;
    search?: string;
    sortBy: string;
  };
}

export interface CharactersFilters {
  page?: number;
  limit?: number;
  category?: string;
  difficulty?: string;
  search?: string;
  sortBy?: "popularity" | "trending" | "recent" | "difficulty";
}

export function useCharacters(filters: CharactersFilters = {}) {
  const { isAuthenticated } = useAuth();
  const [data, setData] = useState<CharactersResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCharacters = async (newFilters: CharactersFilters = {}) => {
    // DEBUG: Temporaneamente disabilitiamo il controllo di autenticazione
    // if (!isAuthenticated) return;

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      
      const allFilters = { ...filters, ...newFilters };
      
      if (allFilters.page) params.set("page", allFilters.page.toString());
      if (allFilters.limit) params.set("limit", allFilters.limit.toString());
      if (allFilters.category) params.set("category", allFilters.category);
      if (allFilters.difficulty) params.set("difficulty", allFilters.difficulty);
      if (allFilters.search) params.set("search", allFilters.search);
      if (allFilters.sortBy) params.set("sortBy", allFilters.sortBy);

      const response = await fetch(`/api/characters?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error("Failed to fetch characters");
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharacters();
  }, []); // DEBUG: Rimuoviamo la dipendenza da isAuthenticated

  return {
    data,
    loading,
    error,
    refetch: fetchCharacters,
  };
}

export function useFavorites() {
  const { isAuthenticated } = useAuth();
  const [favorites, setFavorites] = useState<Character[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFavorites = async () => {
    if (!isAuthenticated) return;

    setLoading(true);
    try {
      const response = await fetch("/api/characters/favorites");
      if (response.ok) {
        const data = await response.json();
        setFavorites(data.favorites);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch favorites");
    } finally {
      setLoading(false);
    }
  };

  const addToFavorites = async (characterId: string) => {
    try {
      const response = await fetch("/api/characters/favorites", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ characterId }),
      });

      if (response.ok) {
        await fetchFavorites(); // Refresh favorites
        return true;
      } else {
        const error = await response.json();
        throw new Error(error.error || "Failed to add to favorites");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add to favorites");
      return false;
    }
  };

  const removeFromFavorites = async (characterId: string) => {
    try {
      const response = await fetch(`/api/characters/favorites?characterId=${characterId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        await fetchFavorites(); // Refresh favorites
        return true;
      } else {
        throw new Error("Failed to remove from favorites");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove from favorites");
      return false;
    }
  };

  const isFavorite = (characterId: string) => {
    return favorites.some(fav => fav.id === characterId);
  };

  useEffect(() => {
    fetchFavorites();
  }, [isAuthenticated]);

  return {
    favorites,
    loading,
    error,
    addToFavorites,
    removeFromFavorites,
    isFavorite,
    refetch: fetchFavorites,
  };
}

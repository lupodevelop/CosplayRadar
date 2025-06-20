"use client";

import { useState } from "react";
import { Search, Filter, X } from "lucide-react";
import { CharactersFilters } from "@/hooks/use-characters";

interface FiltersProps {
  filters: CharactersFilters;
  onFiltersChange: (filters: CharactersFilters) => void;
  onReset: () => void;
}

const categories = [
  { value: "ANIME", label: "Anime" },
  { value: "MANGA", label: "Manga" },
  { value: "VIDEOGAME", label: "Videogiochi" },
  { value: "MOVIE", label: "Film" },
  { value: "TV_SHOW", label: "Serie TV" },
  { value: "COMIC", label: "Comics" },
  { value: "OTHER", label: "Altro" },
];

const difficulties = [
  { value: "1", label: "⭐ Principiante" },
  { value: "2", label: "⭐⭐ Facile" },
  { value: "3", label: "⭐⭐⭐ Intermedio" },
  { value: "4", label: "⭐⭐⭐⭐ Difficile" },
  { value: "5", label: "⭐⭐⭐⭐⭐ Esperto" },
];

const sortOptions = [
  { value: "popularity", label: "Più Popolari" },
  { value: "trending", label: "Trending Ora" },
  { value: "recent", label: "Più Recenti" },
  { value: "difficulty", label: "Difficoltà" },
];

export function CharacterFilters({ filters, onFiltersChange, onReset }: FiltersProps) {
  const [showFilters, setShowFilters] = useState(false);
  const [search, setSearch] = useState(filters.search || "");

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFiltersChange({ ...filters, search: search.trim() || undefined, page: 1 });
  };

  const handleFilterChange = (key: keyof CharactersFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value, page: 1 });
  };

  const hasActiveFilters = filters.category || filters.difficulty || filters.search;

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <form onSubmit={handleSearchSubmit} className="relative">
        <div className="flex">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              placeholder="Cerca personaggi, serie, anime..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-l-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-2 bg-purple-600 text-white rounded-r-md hover:bg-purple-700 focus:ring-2 focus:ring-purple-500"
          >
            Cerca
          </button>
        </div>
      </form>

      {/* Filter Controls */}
      <div className="flex flex-wrap items-center gap-4">
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 focus:ring-2 focus:ring-purple-500"
        >
          <Filter className="h-4 w-4" />
          Filtri
          {hasActiveFilters && (
            <span className="bg-purple-600 text-white text-xs rounded-full px-2 py-1">
              {[filters.category, filters.difficulty, filters.search].filter(Boolean).length}
            </span>
          )}
        </button>

        {/* Sort Dropdown */}
        <select
          value={filters.sortBy || "popularity"}
          onChange={(e) => handleFilterChange("sortBy", e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500"
        >
          {sortOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        {/* Reset Filters */}
        {hasActiveFilters && (
          <button
            onClick={() => {
              setSearch("");
              onReset();
            }}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900"
          >
            <X className="h-4 w-4" />
            Cancella Filtri
          </button>
        )}
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="bg-gray-50 p-4 rounded-lg space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Categoria
              </label>
              <select
                value={filters.category || ""}
                onChange={(e) => handleFilterChange("category", e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Tutte le categorie</option>
                {categories.map((category) => (
                  <option key={category.value} value={category.value}>
                    {category.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Difficulty Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Difficoltà
              </label>
              <select
                value={filters.difficulty || ""}
                onChange={(e) => handleFilterChange("difficulty", e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Tutte le difficoltà</option>
                {difficulties.map((difficulty) => (
                  <option key={difficulty.value} value={difficulty.value}>
                    {difficulty.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="flex flex-wrap gap-2">
          {filters.category && (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full">
              {categories.find(c => c.value === filters.category)?.label}
              <button
                onClick={() => handleFilterChange("category", undefined)}
                className="hover:text-purple-900"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
          {filters.difficulty && (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full">
              {difficulties.find(d => d.value === filters.difficulty)?.label}
              <button
                onClick={() => handleFilterChange("difficulty", undefined)}
                className="hover:text-purple-900"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
          {filters.search && (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full">
              "{filters.search}"
              <button
                onClick={() => {
                  setSearch("");
                  handleFilterChange("search", undefined);
                }}
                className="hover:text-purple-900"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
}

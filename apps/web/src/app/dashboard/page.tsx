"use client";

import { useState } from "react";
import { useAuth } from "@/hooks/use-auth";
import { useCharacters, CharactersFilters } from "@/hooks/use-characters";
import { Navbar } from "@/components/navbar";
import { CharacterFilters } from "@/components/character-filters";
import { CharacterCard } from "@/components/character-card";
import { Pagination } from "@/components/pagination";
import { TrendingUp, Users, Star, BarChart3, Loader2 } from "lucide-react";

export default function DashboardPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [filters, setFilters] = useState<CharactersFilters>({
    page: 1,
    limit: 12,
    sortBy: "trending",
  });

  const { data, loading, error, refetch } = useCharacters(filters);

  const handleFiltersChange = (newFilters: CharactersFilters) => {
    setFilters(newFilters);
    refetch(newFilters);
  };

  const handlePageChange = (page: number) => {
    const newFilters = { ...filters, page };
    setFilters(newFilters);
    refetch(newFilters);
  };

  const resetFilters = () => {
    const resetFilters = { page: 1, limit: 12, sortBy: "trending" as const };
    setFilters(resetFilters);
    refetch(resetFilters);
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">
              Ciao, {user?.name}! 👋
            </h1>
            <p className="mt-2 text-gray-600">
              Scopri i personaggi cosplay più trending del momento
            </p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <TrendingUp className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Personaggi Trending
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {data?.pagination.totalCount || "---"}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Users className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Cosplayer Attivi
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        12,483
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Star className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Tuoi Preferiti
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        23
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <BarChart3 className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Insights Questa Settimana
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        156
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="bg-white rounded-lg shadow mb-6 p-6">
            <CharacterFilters
              filters={filters}
              onFiltersChange={handleFiltersChange}
              onReset={resetFilters}
            />
          </div>

          {/* Characters Grid */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Personaggi Trending
                </h2>
                {data && (
                  <p className="text-sm text-gray-500">
                    {data.pagination.totalCount} risultati trovati
                  </p>
                )}
              </div>

              {/* Loading State */}
              {loading && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
                  <span className="ml-2 text-gray-600">Caricamento personaggi...</span>
                </div>
              )}

              {/* Error State */}
              {error && (
                <div className="text-center py-12">
                  <div className="text-red-600 mb-4">
                    <p className="text-lg font-medium">Errore nel caricamento</p>
                    <p className="text-sm">{error}</p>
                  </div>
                  <button
                    onClick={() => refetch(filters)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    Riprova
                  </button>
                </div>
              )}

              {/* Characters Grid */}
              {data && data.characters.length > 0 && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
                    {data.characters.map((character) => (
                      <CharacterCard key={character.id} character={character} />
                    ))}
                  </div>

                  {/* Pagination */}
                  <Pagination
                    currentPage={data.pagination.page}
                    totalPages={data.pagination.totalPages}
                    hasNext={data.pagination.hasNext}
                    hasPrev={data.pagination.hasPrev}
                    onPageChange={handlePageChange}
                  />
                </>
              )}

              {/* Empty State */}
              {data && data.characters.length === 0 && !loading && (
                <div className="text-center py-12">
                  <div className="text-gray-400 mb-4">
                    <TrendingUp className="h-16 w-16 mx-auto" />
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Nessun personaggio trovato
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Prova a modificare i filtri o la ricerca per trovare altri personaggi.
                  </p>
                  <button
                    onClick={resetFilters}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    Cancella Filtri
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

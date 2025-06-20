"""
Fetcher for upcoming anime releases from AniList
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .anilist_fetcher import AniListFetcher
from ..models import MediaData, MediaType


class UpcomingReleasesFetcher(AniListFetcher):
    """Fetcher for upcoming anime releases"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    async def fetch_upcoming_anime(
        self, 
        months_ahead: int = 3,
        limit: int = 50
    ) -> List[MediaData]:
        """
        Fetch upcoming anime releases in the next X months
        
        Args:
            months_ahead: Number of months to look ahead
            limit: Maximum number of results
        """
        current_year = datetime.now().year
        current_season = self._get_current_season()
        
        # Get current and next seasons
        seasons_to_check = self._get_upcoming_seasons(months_ahead)
        
        all_upcoming = []
        
        for season_year, season in seasons_to_check:
            upcoming = await self._fetch_upcoming_by_season(season, season_year, limit)
            all_upcoming.extend(upcoming)
        
        # Sort by popularity and limit results
        all_upcoming.sort(key=lambda x: x.popularity or 0, reverse=True)
        return all_upcoming[:limit]
    
    async def fetch_recently_released(
        self, 
        weeks_back: int = 4,
        limit: int = 30
    ) -> List[MediaData]:
        """
        Fetch anime released in the last X weeks (per mantenere interesse)
        
        Args:
            weeks_back: Number of weeks to look back
            limit: Maximum number of results
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        query = """
        query ($page: Int, $perPage: Int, $startDateGreater: FuzzyDate, $startDateLesser: FuzzyDate) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    lastPage
                }
                media(
                    type: ANIME,
                    status: RELEASING,
                    startDate_greater: $startDateGreater,
                    startDate_lesser: $startDateLesser,
                    sort: POPULARITY_DESC
                ) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    type
                    format
                    status
                    startDate {
                        year
                        month
                        day
                    }
                    season
                    seasonYear
                    episodes
                    genres
                    popularity
                    favourites
                    averageScore
                    trending
                    coverImage {
                        large
                        medium
                        color
                    }
                    characters(sort: FAVOURITES_DESC, perPage: 10) {
                        edges {
                            role
                            node {
                                id
                                name {
                                    full
                                    native
                                }
                                image {
                                    large
                                    medium
                                }
                                favourites
                                gender
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'page': 1,
            'perPage': limit,
            'startDateGreater': {
                'year': start_date.year,
                'month': start_date.month,
                'day': start_date.day
            },
            'startDateLesser': {
                'year': end_date.year,
                'month': end_date.month,
                'day': end_date.day
            }
        }
        
        try:
            response = await self._make_request(query, variables)
            
            if not response or 'Page' not in response:
                self.logger.warning("No recently released anime found")
                return []
            
            media_list = response['Page']['media']
            timestamp = datetime.now()
            
            result = []
            for media_data in media_list:
                processed = await self._process_media_data(media_data, timestamp, detailed=True)
                if processed:
                    result.append(processed)
            
            self.logger.info(f"📥 Fetched {len(result)} recently released anime")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching recently released anime: {e}")
            raise
    
    async def _fetch_upcoming_by_season(
        self, 
        season: str, 
        year: int, 
        limit: int
    ) -> List[MediaData]:
        """Fetch upcoming anime for a specific season"""
        query = """
        query ($page: Int, $perPage: Int, $season: MediaSeason, $seasonYear: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                }
                media(
                    type: ANIME,
                    season: $season,
                    seasonYear: $seasonYear,
                    status_in: [NOT_YET_RELEASED, RELEASING],
                    sort: POPULARITY_DESC
                ) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    type
                    format
                    status
                    startDate {
                        year
                        month
                        day
                    }
                    season
                    seasonYear
                    episodes
                    genres
                    tags {
                        name
                        rank
                    }
                    popularity
                    favourites
                    averageScore
                    trending
                    coverImage {
                        large
                        medium
                        color
                    }
                    characters(sort: FAVOURITES_DESC, perPage: 15) {
                        edges {
                            role
                            node {
                                id
                                name {
                                    full
                                    native
                                }
                                image {
                                    large
                                    medium
                                }
                                favourites
                                gender
                            }
                        }
                    }
                    studios {
                        nodes {
                            name
                            isAnimationStudio
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'page': 1,
            'perPage': limit,
            'season': season,
            'seasonYear': year
        }
        
        try:
            response = await self._make_request(query, variables)
            
            if not response or 'Page' not in response:
                self.logger.warning(f"No upcoming anime found for {season} {year}")
                return []
            
            media_list = response['Page']['media']
            timestamp = datetime.now()
            
            result = []
            for media_data in media_list:
                processed = await self._process_media_data(media_data, timestamp, detailed=True)
                if processed:
                    result.append(processed)
            
            self.logger.info(f"📥 Fetched {len(result)} upcoming anime for {season} {year}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching upcoming anime for {season} {year}: {e}")
            return []
    
    def _get_current_season(self) -> str:
        """Get current anime season"""
        month = datetime.now().month
        if 3 <= month <= 5:
            return "SPRING"
        elif 6 <= month <= 8:
            return "SUMMER"
        elif 9 <= month <= 11:
            return "FALL"
        else:
            return "WINTER"
    
    def _get_upcoming_seasons(self, months_ahead: int) -> List[tuple]:
        """Get list of (year, season) tuples for upcoming seasons"""
        current_date = datetime.now()
        seasons = []
        
        for i in range(months_ahead + 1):
            future_date = current_date + timedelta(days=i * 30)  # Approximate months
            year = future_date.year
            month = future_date.month
            
            if 3 <= month <= 5:
                season = "SPRING"
            elif 6 <= month <= 8:
                season = "SUMMER"
            elif 9 <= month <= 11:
                season = "FALL"
            else:
                season = "WINTER"
            
            season_tuple = (year, season)
            if season_tuple not in seasons:
                seasons.append(season_tuple)
        
        return seasons
"""
Specialized fetcher for trending anime/manga data from AniList
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .anilist_fetcher import AniListFetcher
from ..models import TrendingScoreData, MediaType


class TrendingFetcher(AniListFetcher):
    """Fetcher for trending anime and manga data"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    async def fetch_trending_anime(
        self, 
        limit: int = 50, 
        max_pages: Optional[int] = None
    ) -> List[TrendingScoreData]:
        """Fetch trending anime data"""
        return await self._fetch_trending_media(MediaType.ANIME, limit, max_pages)
    
    async def fetch_trending_manga(
        self, 
        limit: int = 50, 
        max_pages: Optional[int] = None
    ) -> List[TrendingScoreData]:
        """Fetch trending manga data"""
        return await self._fetch_trending_media(MediaType.MANGA, limit, max_pages)
    
    async def fetch_all_trending(
        self, 
        anime_limit: int = 50, 
        manga_limit: int = 50,
        max_pages: Optional[int] = None
    ) -> Dict[str, List[TrendingScoreData]]:
        """Fetch both trending anime and manga"""
        anime_data = await self.fetch_trending_anime(anime_limit, max_pages)
        manga_data = await self.fetch_trending_manga(manga_limit, max_pages)
        
        return {
            'anime': anime_data,
            'manga': manga_data
        }
    
    async def _fetch_trending_media(
        self, 
        media_type: MediaType, 
        limit: int, 
        max_pages: Optional[int]
    ) -> List[TrendingScoreData]:
        """Internal method to fetch trending media of specific type"""
        query = self.get_trending_query()
        variables = {
            'type': media_type.value,
            'perPage': min(limit, 50)  # AniList max per page
        }
        
        # Calculate max pages based on limit
        if not max_pages:
            max_pages = (limit + 49) // 50  # Round up division
        
        try:
            raw_data = await self.fetch_with_pagination(
                query=query,
                variables=variables,
                data_key='Page',
                page_size=variables['perPage'],
                max_pages=max_pages
            )
            
            trending_data = []
            timestamp = datetime.now()
            
            for page_data in raw_data:
                if 'media' not in page_data:
                    continue
                    
                for media_item in page_data['media']:
                    try:
                        # Extract characters with their roles and details
                        characters = []
                        if 'characters' in media_item and media_item['characters']:
                            for char_edge in media_item['characters'].get('edges', []):
                                char_node = char_edge.get('node', {})
                                if char_node:
                                    character_data = {
                                        'id': char_node.get('id'),
                                        'name': char_node.get('name', {}),
                                        'image': char_node.get('image', {}),
                                        'description': char_node.get('description'),
                                        'gender': char_node.get('gender'),
                                        'age': char_node.get('age'),
                                        'favourites': char_node.get('favourites', 0),
                                        'role': char_edge.get('role'),
                                        'voice_actors': []
                                    }
                                    
                                    # Add voice actors
                                    for va in char_edge.get('voiceActors', []):
                                        character_data['voice_actors'].append({
                                            'id': va.get('id'),
                                            'name': va.get('name', {}).get('full')
                                        })
                                    
                                    characters.append(character_data)
                        
                        # Extract studios
                        studios = []
                        if 'studios' in media_item and media_item['studios']:
                            for studio in media_item['studios'].get('nodes', []):
                                studios.append({
                                    'id': studio.get('id'),
                                    'name': studio.get('name')
                                })
                        
                        # Create TrendingScoreData object
                        trending_item = TrendingScoreData(
                            timestamp=timestamp,
                            media_id=media_item.get('id'),
                            title=media_item.get('title', {}),
                            media_type=media_type,
                            format=media_item.get('format'),
                            status=media_item.get('status'),
                            description=media_item.get('description'),
                            start_date=media_item.get('startDate'),
                            end_date=media_item.get('endDate'),
                            season=media_item.get('season'),
                            season_year=media_item.get('seasonYear'),
                            episodes=media_item.get('episodes'),
                            duration=media_item.get('duration'),
                            chapters=media_item.get('chapters'),
                            volumes=media_item.get('volumes'),
                            genres=media_item.get('genres', []),
                            tags=[
                                {'name': tag.get('name'), 'rank': tag.get('rank')} 
                                for tag in media_item.get('tags', [])
                            ],
                            popularity=media_item.get('popularity', 0),
                            favourites=media_item.get('favourites', 0),
                            average_score=media_item.get('averageScore'),
                            mean_score=media_item.get('meanScore'),
                            trending_rank=media_item.get('trending', 0),
                            cover_image=media_item.get('coverImage', {}),
                            banner_image=media_item.get('bannerImage'),
                            characters=characters,
                            studios=studios
                        )
                        
                        trending_data.append(trending_item)
                        
                        if len(trending_data) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing media item {media_item.get('id', 'unknown')}: {e}")
                        continue
                
                if len(trending_data) >= limit:
                    break
            
            self.logger.info(f"Successfully fetched {len(trending_data)} trending {media_type.value.lower()} items")
            return trending_data[:limit]  # Ensure we don't exceed the limit
            
        except Exception as e:
            self.logger.error(f"Error fetching trending {media_type.value.lower()}: {e}")
            raise
    
    async def fetch_seasonal_anime(
        self,
        year: int,
        season: str,
        limit: int = 50
    ) -> List[TrendingScoreData]:
        """Fetch anime from specific season"""
        query = """
        query ($year: Int, $season: MediaSeason, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    perPage
                }
                media(seasonYear: $year, season: $season, type: ANIME, sort: POPULARITY_DESC) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    type
                    format
                    status
                    description
                    startDate {
                        year
                        month
                        day
                    }
                    endDate {
                        year
                        month
                        day
                    }
                    season
                    seasonYear
                    episodes
                    duration
                    genres
                    tags {
                        name
                        rank
                    }
                    popularity
                    favourites
                    averageScore
                    meanScore
                    trending
                    coverImage {
                        large
                        medium
                    }
                    bannerImage
                    characters(sort: FAVOURITES_DESC, perPage: 10) {
                        edges {
                            role
                            voiceActors(language: JAPANESE) {
                                id
                                name {
                                    full
                                }
                            }
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
                                description
                                gender
                                age
                                favourites
                            }
                        }
                    }
                    studios {
                        nodes {
                            id
                            name
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'year': year,
            'season': season.upper(),
            'perPage': min(limit, 50)
        }
        
        try:
            raw_data = await self.fetch_with_pagination(
                query=query,
                variables=variables,
                data_key='Page',
                page_size=variables['perPage'],
                max_pages=(limit + 49) // 50
            )
            
            seasonal_data = []
            timestamp = datetime.now()
            
            for page_data in raw_data:
                if 'media' not in page_data:
                    continue
                    
                for media_item in page_data['media']:
                    try:
                        # Process characters
                        characters = []
                        if 'characters' in media_item and media_item['characters']:
                            for char_edge in media_item['characters'].get('edges', []):
                                char_node = char_edge.get('node', {})
                                if char_node:
                                    character_data = {
                                        'id': char_node.get('id'),
                                        'name': char_node.get('name', {}),
                                        'image': char_node.get('image', {}),
                                        'description': char_node.get('description'),
                                        'gender': char_node.get('gender'),
                                        'age': char_node.get('age'),
                                        'favourites': char_node.get('favourites', 0),
                                        'role': char_edge.get('role'),
                                        'voice_actors': [
                                            {
                                                'id': va.get('id'),
                                                'name': va.get('name', {}).get('full')
                                            }
                                            for va in char_edge.get('voiceActors', [])
                                        ]
                                    }
                                    characters.append(character_data)
                        
                        # Process studios
                        studios = []
                        if 'studios' in media_item and media_item['studios']:
                            for studio in media_item['studios'].get('nodes', []):
                                studios.append({
                                    'id': studio.get('id'),
                                    'name': studio.get('name')
                                })
                        
                        seasonal_item = TrendingScoreData(
                            timestamp=timestamp,
                            media_id=media_item.get('id'),
                            title=media_item.get('title', {}),
                            media_type=MediaType.ANIME,
                            format=media_item.get('format'),
                            status=media_item.get('status'),
                            description=media_item.get('description'),
                            start_date=media_item.get('startDate'),
                            end_date=media_item.get('endDate'),
                            season=media_item.get('season'),
                            season_year=media_item.get('seasonYear'),
                            episodes=media_item.get('episodes'),
                            duration=media_item.get('duration'),
                            chapters=None,
                            volumes=None,
                            genres=media_item.get('genres', []),
                            tags=[
                                {'name': tag.get('name'), 'rank': tag.get('rank')} 
                                for tag in media_item.get('tags', [])
                            ],
                            popularity=media_item.get('popularity', 0),
                            favourites=media_item.get('favourites', 0),
                            average_score=media_item.get('averageScore'),
                            mean_score=media_item.get('meanScore'),
                            trending_rank=media_item.get('trending', 0),
                            cover_image=media_item.get('coverImage', {}),
                            banner_image=media_item.get('bannerImage'),
                            characters=characters,
                            studios=studios
                        )
                        
                        seasonal_data.append(seasonal_item)
                        
                        if len(seasonal_data) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing seasonal media item {media_item.get('id', 'unknown')}: {e}")
                        continue
                
                if len(seasonal_data) >= limit:
                    break
            
            self.logger.info(f"Successfully fetched {len(seasonal_data)} seasonal anime for {season} {year}")
            return seasonal_data[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching seasonal anime for {season} {year}: {e}")
            raise

"""
Specialized fetcher for media (anime/manga) data from AniList
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .anilist_fetcher import AniListFetcher
from ..models import MediaData, MediaType


class MediaFetcher(AniListFetcher):
    """Fetcher for anime and manga media data"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    async def fetch_popular_anime(
        self, 
        limit: int = 50, 
        max_pages: Optional[int] = None
    ) -> List[MediaData]:
        """Fetch popular anime by popularity score"""
        return await self._fetch_popular_media(MediaType.ANIME, limit, max_pages)
    
    async def fetch_popular_manga(
        self, 
        limit: int = 50, 
        max_pages: Optional[int] = None
    ) -> List[MediaData]:
        """Fetch popular manga by popularity score"""
        return await self._fetch_popular_media(MediaType.MANGA, limit, max_pages)
    
    async def fetch_top_rated_anime(
        self, 
        limit: int = 50, 
        max_pages: Optional[int] = None
    ) -> List[MediaData]:
        """Fetch top rated anime by average score"""
        return await self._fetch_top_rated_media(MediaType.ANIME, limit, max_pages)
    
    async def fetch_top_rated_manga(
        self, 
        limit: int = 50, 
        max_pages: Optional[int] = None
    ) -> List[MediaData]:
        """Fetch top rated manga by average score"""
        return await self._fetch_top_rated_media(MediaType.MANGA, limit, max_pages)
    
    async def fetch_media_by_id(self, media_id: int) -> Optional[MediaData]:
        """Fetch detailed information for a specific media"""
        query = """
        query ($id: Int) {
            Media(id: $id) {
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
                chapters
                volumes
                genres
                tags {
                    name
                    rank
                    category
                }
                popularity
                favourites
                averageScore
                meanScore
                trending
                coverImage {
                    large
                    medium
                    color
                }
                bannerImage
                characters(sort: FAVOURITES_DESC, perPage: 25) {
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
                        isAnimationStudio
                    }
                }
                relations {
                    edges {
                        relationType
                        node {
                            id
                            title {
                                romaji
                                english
                            }
                            type
                            format
                            coverImage {
                                medium
                            }
                        }
                    }
                }
                recommendations {
                    edges {
                        rating
                        node {
                            mediaRecommendation {
                                id
                                title {
                                    romaji
                                    english
                                }
                                type
                                format
                                averageScore
                                coverImage {
                                    medium
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {'id': media_id}
        
        try:
            response = await self._make_request(query, variables)
            
            if not response or 'Media' not in response:
                self.logger.warning(f"No media found with ID {media_id}")
                return None
            
            media_data = response['Media']
            timestamp = datetime.now()
            
            return await self._process_media_data(media_data, timestamp, detailed=True)
            
        except Exception as e:
            self.logger.error(f"Error fetching media {media_id}: {e}")
            raise
    
    async def search_media(
        self,
        search_term: str,
        media_type: Optional[MediaType] = None,
        limit: int = 50
    ) -> List[MediaData]:
        """Search for media by title"""
        query = """
        query ($search: String, $type: MediaType, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    perPage
                }
                media(search: $search, type: $type, sort: POPULARITY_DESC) {
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
                    season
                    seasonYear
                    episodes
                    duration
                    chapters
                    volumes
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
                                gender
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
            'search': search_term,
            'perPage': min(limit, 50)
        }
        
        if media_type:
            variables['type'] = media_type.value
        
        try:
            raw_data = await self.fetch_with_pagination(
                query=query,
                variables=variables,
                data_key='Page',
                page_size=variables['perPage'],
                max_pages=(limit + 49) // 50
            )
            
            media_list = []
            timestamp = datetime.now()
            
            for page_data in raw_data:
                if 'media' not in page_data:
                    continue
                    
                for media_item in page_data['media']:
                    try:
                        media_data = await self._process_media_data(media_item, timestamp)
                        media_list.append(media_data)
                        
                        if len(media_list) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing media {media_item.get('id', 'unknown')}: {e}")
                        continue
                
                if len(media_list) >= limit:
                    break
            
            self.logger.info(f"Successfully found {len(media_list)} media matching '{search_term}'")
            return media_list[:limit]
            
        except Exception as e:
            self.logger.error(f"Error searching media for '{search_term}': {e}")
            raise
    
    async def fetch_trending_anime(
        self, 
        limit: int = 50, 
        max_pages: Optional[int] = None
    ) -> List[MediaData]:
        """Fetch currently trending anime"""
        return await self._fetch_trending_media(MediaType.ANIME, limit, max_pages)
    
    async def fetch_trending_manga(
        self, 
        limit: int = 50, 
        max_pages: Optional[int] = None
    ) -> List[MediaData]:
        """Fetch currently trending manga"""
        return await self._fetch_trending_media(MediaType.MANGA, limit, max_pages)
    
    async def fetch_upcoming_anime(
        self, 
        limit: int = 50, 
        max_pages: Optional[int] = None
    ) -> List[MediaData]:
        """Fetch upcoming anime releases"""
        return await self._fetch_upcoming_media(MediaType.ANIME, limit, max_pages)
    
    async def fetch_recently_released_anime(
        self, 
        limit: int = 50, 
        max_pages: Optional[int] = None
    ) -> List[MediaData]:
        """Fetch recently released anime (last 30 days)"""
        return await self._fetch_recently_released_media(MediaType.ANIME, limit, max_pages)
    
    async def fetch_current_season_anime(
        self, 
        limit: int = 50, 
        max_pages: Optional[int] = None
    ) -> List[MediaData]:
        """Fetch anime from current season"""
        return await self._fetch_current_season_media(MediaType.ANIME, limit, max_pages)
    
    async def _fetch_popular_media(
        self, 
        media_type: MediaType, 
        limit: int, 
        max_pages: Optional[int]
    ) -> List[MediaData]:
        """Internal method to fetch popular media of specific type"""
        query = """
        query ($type: MediaType, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    perPage
                }
                media(type: $type, sort: POPULARITY_DESC) {
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
                    chapters
                    volumes
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
            'type': media_type.value,
            'perPage': min(limit, 50)
        }
        
        if not max_pages:
            max_pages = (limit + 49) // 50
        
        try:
            raw_data = await self.fetch_with_pagination(
                query=query,
                variables=variables,
                data_key='Page',
                page_size=variables['perPage'],
                max_pages=max_pages
            )
            
            media_list = []
            timestamp = datetime.now()
            
            for page_data in raw_data:
                if 'media' not in page_data:
                    continue
                    
                for media_item in page_data['media']:
                    try:
                        media_data = await self._process_media_data(media_item, timestamp)
                        media_list.append(media_data)
                        
                        if len(media_list) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing media {media_item.get('id', 'unknown')}: {e}")
                        continue
                
                if len(media_list) >= limit:
                    break
            
            self.logger.info(f"Successfully fetched {len(media_list)} popular {media_type.value.lower()} items")
            return media_list[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching popular {media_type.value.lower()}: {e}")
            raise
    
    async def _fetch_top_rated_media(
        self, 
        media_type: MediaType, 
        limit: int, 
        max_pages: Optional[int]
    ) -> List[MediaData]:
        """Internal method to fetch top rated media of specific type"""
        query = """
        query ($type: MediaType, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    perPage
                }
                media(type: $type, sort: SCORE_DESC) {
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
                    chapters
                    volumes
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
            'type': media_type.value,
            'perPage': min(limit, 50)
        }
        
        if not max_pages:
            max_pages = (limit + 49) // 50
        
        try:
            raw_data = await self.fetch_with_pagination(
                query=query,
                variables=variables,
                data_key='Page',
                page_size=variables['perPage'],
                max_pages=max_pages
            )
            
            media_list = []
            timestamp = datetime.now()
            
            for page_data in raw_data:
                if 'media' not in page_data:
                    continue
                    
                for media_item in page_data['media']:
                    try:
                        media_data = await self._process_media_data(media_item, timestamp)
                        media_list.append(media_data)
                        
                        if len(media_list) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing media {media_item.get('id', 'unknown')}: {e}")
                        continue
                
                if len(media_list) >= limit:
                    break
            
            self.logger.info(f"Successfully fetched {len(media_list)} top rated {media_type.value.lower()} items")
            return media_list[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching top rated {media_type.value.lower()}: {e}")
            raise
    
    async def _fetch_trending_media(
        self, 
        media_type: MediaType, 
        limit: int, 
        max_pages: Optional[int]
    ) -> List[MediaData]:
        """Internal method to fetch trending media of specific type"""
        query = """
        query ($type: MediaType, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    perPage
                }
                media(type: $type, sort: TRENDING_DESC) {
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
                    chapters
                    volumes
                    genres
                    tags {
                        name
                        rank
                        category
                    }
                    popularity
                    favourites
                    averageScore
                    meanScore
                    trending
                    coverImage {
                        large
                        medium
                        color
                    }
                    bannerImage
                    characters(sort: FAVOURITES_DESC, perPage: 25) {
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
                                gender
                                favourites
                            }
                        }
                    }
                    studios {
                        edges {
                            node {
                                id
                                name
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'type': media_type.value,
            'perPage': min(limit, 50)
        }
        
        if not max_pages:
            max_pages = (limit + 49) // 50
        
        try:
            raw_data = await self.fetch_with_pagination(
                query=query,
                variables=variables,
                data_key='Page',
                page_size=variables['perPage'],
                max_pages=max_pages
            )
            
            media_list = []
            timestamp = datetime.now()
            
            for page_data in raw_data:
                if 'media' not in page_data:
                    continue
                    
                for media_item in page_data['media']:
                    try:
                        media_data = await self._process_media_data(media_item, timestamp)
                        media_list.append(media_data)
                        
                        if len(media_list) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing media {media_item.get('id', 'unknown')}: {e}")
                        continue
                
                if len(media_list) >= limit:
                    break
            
            self.logger.info(f"Successfully fetched {len(media_list)} trending {media_type.value.lower()} items")
            return media_list[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching trending {media_type.value.lower()}: {e}")
            raise
    
    async def _fetch_upcoming_media(
        self, 
        media_type: MediaType, 
        limit: int, 
        max_pages: Optional[int]
    ) -> List[MediaData]:
        """Internal method to fetch upcoming media releases"""
        from datetime import datetime
        current_year = datetime.now().year
        
        query = """
        query ($type: MediaType, $page: Int, $perPage: Int, $year: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    perPage
                }
                media(type: $type, status: NOT_YET_RELEASED, seasonYear_greater: $year, sort: POPULARITY_DESC) {
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
                    season
                    seasonYear
                    episodes
                    duration
                    genres
                    tags {
                        name
                        rank
                        category
                    }
                    popularity
                    favourites
                    averageScore
                    meanScore
                    trending
                    coverImage {
                        large
                        medium
                        color
                    }
                    bannerImage
                    characters(sort: FAVOURITES_DESC, perPage: 25) {
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
                                gender
                                favourites
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'type': media_type.value,
            'year': current_year - 1,
            'perPage': min(limit, 50)
        }
        
        if not max_pages:
            max_pages = (limit + 49) // 50
        
        try:
            raw_data = await self.fetch_with_pagination(
                query=query,
                variables=variables,
                data_key='Page',
                page_size=variables['perPage'],
                max_pages=max_pages
            )
            
            media_list = []
            timestamp = datetime.now()
            
            for page_data in raw_data:
                if 'media' not in page_data:
                    continue
                    
                for media_item in page_data['media']:
                    try:
                        media_data = await self._process_media_data(media_item, timestamp)
                        media_list.append(media_data)
                        
                        if len(media_list) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing media {media_item.get('id', 'unknown')}: {e}")
                        continue
                
                if len(media_list) >= limit:
                    break
            
            self.logger.info(f"Successfully fetched {len(media_list)} upcoming {media_type.value.lower()} items")
            return media_list[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching upcoming {media_type.value.lower()}: {e}")
            raise
    
    async def _fetch_recently_released_media(
        self, 
        media_type: MediaType, 
        limit: int, 
        max_pages: Optional[int]
    ) -> List[MediaData]:
        """Internal method to fetch recently released media (last 30 days)"""
        from datetime import datetime
        current_year = datetime.now().year
        
        query = """
        query ($type: MediaType, $page: Int, $perPage: Int, $year: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    perPage
                }
                media(type: $type, status: RELEASING, seasonYear: $year, sort: POPULARITY_DESC) {
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
                    season
                    seasonYear
                    episodes
                    duration
                    genres
                    tags {
                        name
                        rank
                        category
                    }
                    popularity
                    favourites
                    averageScore
                    meanScore
                    trending
                    coverImage {
                        large
                        medium
                        color
                    }
                    bannerImage
                    characters(sort: FAVOURITES_DESC, perPage: 25) {
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
                                gender
                                favourites
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'type': media_type.value,
            'year': current_year,
            'perPage': min(limit, 50)
        }
        
        if not max_pages:
            max_pages = (limit + 49) // 50
        
        try:
            raw_data = await self.fetch_with_pagination(
                query=query,
                variables=variables,
                data_key='Page',
                page_size=variables['perPage'],
                max_pages=max_pages
            )
            
            media_list = []
            timestamp = datetime.now()
            
            for page_data in raw_data:
                if 'media' not in page_data:
                    continue
                    
                for media_item in page_data['media']:
                    try:
                        media_data = await self._process_media_data(media_item, timestamp)
                        media_list.append(media_data)
                        
                        if len(media_list) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing media {media_item.get('id', 'unknown')}: {e}")
                        continue
                
                if len(media_list) >= limit:
                    break
            
            self.logger.info(f"Successfully fetched {len(media_list)} recently released {media_type.value.lower()} items")
            return media_list[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching recently released {media_type.value.lower()}: {e}")
            raise
    
    async def _fetch_current_season_media(
        self, 
        media_type: MediaType, 
        limit: int, 
        max_pages: Optional[int]
    ) -> List[MediaData]:
        """Internal method to fetch current season media"""
        from datetime import datetime
        
        # Determinare la stagione corrente
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        if current_month in [12, 1, 2]:
            season = "WINTER"
        elif current_month in [3, 4, 5]:
            season = "SPRING"
        elif current_month in [6, 7, 8]:
            season = "SUMMER"
        else:
            season = "FALL"
        
        query = """
        query ($type: MediaType, $page: Int, $perPage: Int, $season: MediaSeason, $year: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    perPage
                }
                media(type: $type, season: $season, seasonYear: $year, sort: POPULARITY_DESC) {
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
                    season
                    seasonYear
                    episodes
                    duration
                    genres
                    tags {
                        name
                        rank
                        category
                    }
                    popularity
                    favourites
                    averageScore
                    meanScore
                    trending
                    coverImage {
                        large
                        medium
                        color
                    }
                    bannerImage
                    characters(sort: FAVOURITES_DESC, perPage: 25) {
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
                                gender
                                favourites
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'type': media_type.value,
            'season': season,
            'year': current_year,
            'perPage': min(limit, 50)
        }
        
        if not max_pages:
            max_pages = (limit + 49) // 50
        
        try:
            raw_data = await self.fetch_with_pagination(
                query=query,
                variables=variables,
                data_key='Page',
                page_size=variables['perPage'],
                max_pages=max_pages
            )
            
            media_list = []
            timestamp = datetime.now()
            
            for page_data in raw_data:
                if 'media' not in page_data:
                    continue
                    
                for media_item in page_data['media']:
                    try:
                        media_data = await self._process_media_data(media_item, timestamp)
                        media_list.append(media_data)
                        
                        if len(media_list) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing media {media_item.get('id', 'unknown')}: {e}")
                        continue
                
                if len(media_list) >= limit:
                    break
            
            self.logger.info(f"Successfully fetched {len(media_list)} current season {media_type.value.lower()} items")
            return media_list[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching current season {media_type.value.lower()}: {e}")
            raise
    
    async def _process_media_data(
        self, 
        media_item: Dict[str, Any], 
        timestamp: datetime,
        detailed: bool = False
    ) -> MediaData:
        """Process raw media data into MediaData object"""
        
        # Process characters
        characters = []
        if 'characters' in media_item and media_item['characters']:
            for char_edge in media_item['characters'].get('edges', []):
                char_node = char_edge.get('node', {})
                if char_node:
                    character_info = {
                        'character_id': char_node.get('id'),
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
                    characters.append(character_info)
        
        # Process studios
        studios = []
        if 'studios' in media_item and media_item['studios']:
            for studio in media_item['studios'].get('nodes', []):
                studios.append({
                    'id': studio.get('id'),
                    'name': studio.get('name'),
                    'is_animation_studio': studio.get('isAnimationStudio', False)
                })
        
        # Process relations (for detailed view)
        relations = []
        if detailed and 'relations' in media_item and media_item['relations']:
            for relation_edge in media_item['relations'].get('edges', []):
                relation_node = relation_edge.get('node', {})
                if relation_node:
                    relations.append({
                        'relation_type': relation_edge.get('relationType'),
                        'media_id': relation_node.get('id'),
                        'title': relation_node.get('title', {}),
                        'type': relation_node.get('type'),
                        'format': relation_node.get('format'),
                        'cover_image': relation_node.get('coverImage', {})
                    })
        
        # Process recommendations (for detailed view)
        recommendations = []
        if detailed and 'recommendations' in media_item and media_item['recommendations']:
            for rec_edge in media_item['recommendations'].get('edges', []):
                rec_media = rec_edge.get('node', {}).get('mediaRecommendation', {})
                if rec_media:
                    recommendations.append({
                        'rating': rec_edge.get('rating', 0),
                        'media_id': rec_media.get('id'),
                        'title': rec_media.get('title', {}),
                        'type': rec_media.get('type'),
                        'format': rec_media.get('format'),
                        'average_score': rec_media.get('averageScore'),
                        'cover_image': rec_media.get('coverImage', {})
                    })
        
        # Determine media type
        media_type_str = media_item.get('type', 'ANIME')
        media_type = MediaType.ANIME if media_type_str == 'ANIME' else MediaType.MANGA
        
        media_data = MediaData(
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
                {
                    'name': tag.get('name'), 
                    'rank': tag.get('rank'),
                    'category': tag.get('category')
                } 
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
            studios=studios,
            relations=relations if detailed else [],
            recommendations=recommendations if detailed else []
        )
        
        return media_data

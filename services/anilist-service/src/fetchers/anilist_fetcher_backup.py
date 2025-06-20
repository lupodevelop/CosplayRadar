"""
AniList API Fetcher
Servizio per il fetching di dati da AniList GraphQL API
"""
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..models import AniListConfig
from ..database.repositories.anilist_character_repository import AniListCharacterRepository
from ..database.schema import AniListCharacter, AniListMedia


class AniListFetcher:
    """Fetcher per dati AniList"""
    
    def __init__(self, config: AniListConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.request_timeout),
            connector=aiohttp.TCPConnector(limit=self.config.max_concurrent_requests)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_popular_characters(self, page: int = 1, per_page: int = 50) -> List[Dict[str, Any]]:
        """Fetch dei personaggi più popolari da AniList"""
        query = """
        query ($page: Int, $perPage: Int) {
            Page (page: $page, perPage: $perPage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                    perPage
                }
                characters (sort: FAVOURITES_DESC) {
                    id
                    name {
                        full
                        first
                        middle
                        last
                        native
                        alternative
                        alternativeSpoiler
                    }
                    image {
                        large
                        medium
                    }
                    description
                    gender
                    age
                    bloodType
                    dateOfBirth {
                        year
                        month
                        day
                    }
                    favourites
                    isFavourite
                    isFavouriteBlocked
                    siteUrl
                    modNotes
                    media {
                        edges {
                            node {
                                id
                                title {
                                    romaji
                                    english
                                    native
                                }
                                type
                                format
                                status
                                averageScore
                                popularity
                                favourites
                            }
                            characterRole
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "page": page,
            "perPage": per_page
        }
        
        return await self._execute_query(query, variables)
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits"""
        now = datetime.now()
        
        # Reset window if enough time has passed
        if now - self.rate_limit_state.window_start >= timedelta(seconds=self.RATE_LIMIT_WINDOW):
            self.rate_limit_state.window_start = now
            self.rate_limit_state.requests_in_window = 0
        
        # Check if we need to wait
        if self.rate_limit_state.requests_in_window >= self.RATE_LIMIT_REQUESTS:
            wait_time = self.RATE_LIMIT_WINDOW - (now - self.rate_limit_state.window_start).total_seconds()
            if wait_time > 0:
                self.logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                # Reset after waiting
                self.rate_limit_state.window_start = datetime.now()
                self.rate_limit_state.requests_in_window = 0
    
    async def _make_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GraphQL request with rate limiting and error handling"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        await self._wait_for_rate_limit()
        
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        try:
            self.rate_limit_state.requests_in_window += 1
            self.rate_limit_state.last_request_time = datetime.now()
            
            async with self.session.post(self.API_URL, json=payload) as response:
                response_data = await response.json()
                
                if response.status == 429:
                    # Rate limited, wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._make_request(query, variables)
                
                if response.status != 200:
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"HTTP {response.status}: {response_data}"
                    )
                
                if 'errors' in response_data:
                    error_messages = [error.get('message', 'Unknown error') for error in response_data['errors']]
                    raise ValueError(f"GraphQL errors: {'; '.join(error_messages)}")
                
                return response_data.get('data', {})
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode JSON response: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            raise
    
    async def fetch_with_pagination(
        self, 
        query: str, 
        variables: Dict[str, Any],
        data_key: str,
        page_size: int = 50,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch data with automatic pagination"""
        all_data = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            current_variables = {
                **variables,
                'page': page,
                'perPage': page_size
            }
            
            try:
                response = await self._make_request(query, current_variables)
                
                if not response or data_key not in response:
                    break
                
                page_data = response[data_key]
                if not page_data:
                    break
                
                # Handle different response structures
                if isinstance(page_data, dict):
                    # Structure like { data: [...], pageInfo: {...} }
                    if 'data' in page_data:
                        items = page_data['data']
                        has_next = page_data.get('pageInfo', {}).get('hasNextPage', False)
                    else:
                        # Direct data structure
                        items = [page_data] if page_data else []
                        has_next = False
                elif isinstance(page_data, list):
                    # Direct list structure
                    items = page_data
                    has_next = len(items) == page_size
                else:
                    break
                
                all_data.extend(items)
                
                if not has_next or len(items) < page_size:
                    break
                
                page += 1
                
                # Small delay between requests to be respectful
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error fetching page {page}: {e}")
                break
        
        self.logger.info(f"Fetched {len(all_data)} items across {page} pages")
        return all_data
    
    def get_trending_query(self) -> str:
        """Get trending anime/manga query"""
        return """
        query ($page: Int, $perPage: Int, $type: MediaType) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    perPage
                }
                media(sort: TRENDING_DESC, type: $type) {
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
                    characters(sort: FAVOURITES_DESC) {
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
    
    def get_character_query(self) -> str:
        """Get character details query"""
        return """
        query ($id: Int, $page: Int, $perPage: Int) {
            Character(id: $id) {
                id
                name {
                    full
                    native
                    alternative
                }
                image {
                    large
                    medium
                }
                description
                gender
                age
                favourites
                media(page: $page, perPage: $perPage, sort: FAVOURITES_DESC) {
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
                            title {
                                romaji
                                english
                                native
                            }
                            type
                            format
                            averageScore
                            popularity
                            favourites
                            trending
                            coverImage {
                                large
                                medium
                            }
                        }
                    }
                    pageInfo {
                        hasNextPage
                        currentPage
                    }
                }
            }
        }
        """
    
    def get_popular_characters_query(self) -> str:
        """Get popular characters query"""
        return """
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    perPage
                }
                characters(sort: FAVOURITES_DESC) {
                    id
                    name {
                        full
                        native
                        alternative
                    }
                    image {
                        large
                        medium
                    }
                    description
                    gender
                    age
                    favourites
                    media(perPage: 10, sort: FAVOURITES_DESC) {
                        edges {
                            role
                            node {
                                id
                                title {
                                    romaji
                                    english
                                    native
                                }
                                type
                                format
                                averageScore
                                popularity
                                favourites
                                trending
                                coverImage {
                                    large
                                    medium
                                }
                            }
                        }
                    }
                }
            }
        }
        """

"""
AniList API Fetcher - Complete Implementation
Servizio completo per il fetching di dati da AniList GraphQL API
"""
import asyncio
import aiohttp
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..models import AniListConfig
from ..database.repositories.anilist_character_repository import AniListCharacterRepository
from ..database.schema import AniListCharacter, AniListMedia


@dataclass
class RateLimitState:
    """Track rate limiting state"""
    last_request_time: datetime
    requests_in_window: int
    window_start: datetime
    
    def __post_init__(self):
        now = datetime.now()
        if not hasattr(self, 'last_request_time'):
            self.last_request_time = now
        if not hasattr(self, 'window_start'):
            self.window_start = now


class AniListFetcher:
    """Complete AniList API Fetcher with rate limiting and error handling"""
    
    def __init__(self, config: AniListConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_state = RateLimitState(
            last_request_time=datetime.now(),
            requests_in_window=0,
            window_start=datetime.now()
        )
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.anilist.request_timeout),
            connector=aiohttp.TCPConnector(limit=self.config.anilist.max_concurrent_requests),
            headers={'Content-Type': 'application/json', 'Accept': 'application/json'}
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
        if now - self.rate_limit_state.window_start >= timedelta(seconds=60):
            self.rate_limit_state.window_start = now
            self.rate_limit_state.requests_in_window = 0
        
        # Check if we need to wait
        if self.rate_limit_state.requests_in_window >= self.config.anilist.rate_limit_per_minute:
            wait_time = 60 - (now - self.rate_limit_state.window_start).total_seconds()
            if wait_time > 0:
                self.logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                self.rate_limit_state.window_start = datetime.now()
                self.rate_limit_state.requests_in_window = 0
    
    async def _execute_query(self, query: str, variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute GraphQL query with rate limiting and error handling"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        await self._wait_for_rate_limit()
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        try:
            self.rate_limit_state.requests_in_window += 1
            self.rate_limit_state.last_request_time = datetime.now()
            
            async with self.session.post(self.config.anilist.api_url, json=payload) as response:
                
                if response.status == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    return await self._execute_query(query, variables)
                
                if response.status != 200:
                    self.logger.error(f"AniList API error: {response.status}")
                    return None
                
                response_data = await response.json()
                
                if "errors" in response_data:
                    self.logger.error(f"GraphQL errors: {response_data['errors']}")
                    return None
                
                return response_data.get("data")
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode JSON response: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to fetch from AniList: {e}")
            return None
    
    async def fetch_popular_characters(self, page: int = 1, per_page: int = 50) -> Optional[Dict[str, Any]]:
        """Fetch most popular characters from AniList"""
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
                }
            }
        }
        """
        
        variables = {"page": page, "perPage": per_page}
        return await self._execute_query(query, variables)
    
    async def fetch_trending_media(self, media_type: str = "ANIME", page: int = 1, per_page: int = 50) -> Optional[Dict[str, Any]]:
        """Fetch trending anime/manga"""
        query = """
        query ($page: Int, $perPage: Int, $type: MediaType) {
            Page (page: $page, perPage: $perPage) {
                pageInfo {
                    total
                    currentPage
                    lastPage
                    hasNextPage
                    perPage
                }
                media (sort: TRENDING_DESC, type: $type) {
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
                    trending
                    characters (sort: FAVOURITES_DESC, perPage: 10) {
                        edges {
                            node {
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
                            }
                            characterRole
                        }
                    }
                }
            }
        }
        """
        
        variables = {"page": page, "perPage": per_page, "type": media_type}
        return await self._execute_query(query, variables)
    
    async def fetch_character_by_id(self, character_id: int) -> Optional[Dict[str, Any]]:
        """Fetch specific character by ID"""
        query = """
        query ($id: Int) {
            Character (id: $id) {
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
            }
        }
        """
        
        variables = {"id": character_id}
        result = await self._execute_query(query, variables)
        return result.get("Character") if result else None
    
    def parse_character_data(self, character_data: Dict[str, Any]) -> AniListCharacter:
        """Convert AniList data to AniListCharacter object"""
        name = character_data.get("name", {})
        image = character_data.get("image", {})
        birth_date = character_data.get("dateOfBirth", {})
        
        return AniListCharacter(
            id=character_data["id"],
            name_full=name.get("full"),
            name_first=name.get("first"),
            name_middle=name.get("middle"),
            name_last=name.get("last"),
            name_native=name.get("native"),
            name_alternative=name.get("alternative", []),
            name_alternative_spoiler=name.get("alternativeSpoiler", []),
            image_large=image.get("large"),
            image_medium=image.get("medium"),
            description=character_data.get("description"),
            gender=character_data.get("gender"),
            age=character_data.get("age"),
            blood_type=character_data.get("bloodType"),
            birth_year=birth_date.get("year"),
            birth_month=birth_date.get("month"),
            birth_day=birth_date.get("day"),
            favourites=character_data.get("favourites", 0),
            is_favourite=character_data.get("isFavourite", False),
            is_favourite_blocked=character_data.get("isFavouriteBlocked", False),
            site_url=character_data.get("siteUrl"),
            mod_notes=character_data.get("modNotes"),
            last_fetched_at=datetime.utcnow()
        )


class AniListSyncService:
    """Service for syncing AniList data"""
    
    def __init__(self, fetcher: AniListFetcher, repository: AniListCharacterRepository):
        self.fetcher = fetcher
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    async def sync_popular_characters(self, max_pages: int = 5) -> Dict[str, int]:
        """Sync most popular characters"""
        results = {"synced": 0, "errors": 0, "skipped": 0}
        
        self.logger.info(f"Starting sync of popular characters (max {max_pages} pages)")
        
        for page in range(1, max_pages + 1):
            try:
                self.logger.info(f"Syncing popular characters page {page}")
                
                data = await self.fetcher.fetch_popular_characters(page=page, per_page=50)
                if not data or "Page" not in data:
                    self.logger.warning(f"No data for page {page}")
                    continue
                
                characters = data["Page"]["characters"]
                self.logger.info(f"Processing {len(characters)} characters from page {page}")
                
                for char_data in characters:
                    try:
                        character = self.fetcher.parse_character_data(char_data)
                        
                        # Upsert in database
                        if self.repository.upsert_character(character):
                            results["synced"] += 1
                            if results["synced"] % 10 == 0:
                                self.logger.info(f"Synced {results['synced']} characters so far...")
                        else:
                            results["skipped"] += 1
                            
                    except Exception as e:
                        self.logger.error(f"Error processing character {char_data.get('id', 'unknown')}: {e}")
                        results["errors"] += 1
                
                # Rate limiting between pages
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error syncing page {page}: {e}")
                results["errors"] += 1
        
        self.logger.info(f"Sync completed: {results}")
        return results
    
    async def sync_character_by_id(self, character_id: int) -> bool:
        """Sync specific character by ID"""
        try:
            self.logger.info(f"Syncing character {character_id}")
            
            char_data = await self.fetcher.fetch_character_by_id(character_id)
            if not char_data:
                self.logger.warning(f"No data found for character {character_id}")
                return False
            
            character = self.fetcher.parse_character_data(char_data)
            success = self.repository.upsert_character(character)
            
            if success:
                self.logger.info(f"Successfully synced character {character_id}: {character.name_full}")
            else:
                self.logger.warning(f"Failed to sync character {character_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error syncing character {character_id}: {e}")
            return False
    
    async def sync_trending_characters(self, max_pages: int = 3) -> Dict[str, int]:
        """Sync characters from trending media"""
        results = {"synced": 0, "errors": 0, "skipped": 0}
        
        self.logger.info(f"Starting sync of trending characters (max {max_pages} pages)")
        
        for page in range(1, max_pages + 1):
            try:
                self.logger.info(f"Syncing trending media page {page}")
                
                data = await self.fetcher.fetch_trending_media(page=page, per_page=25)
                if not data or "Page" not in data:
                    self.logger.warning(f"No trending data for page {page}")
                    continue
                
                media_list = data["Page"]["media"]
                
                for media in media_list:
                    if "characters" not in media or not media["characters"]["edges"]:
                        continue
                    
                    for char_edge in media["characters"]["edges"]:
                        char_data = char_edge["node"]
                        try:
                            character = self.fetcher.parse_character_data(char_data)
                            
                            if self.repository.upsert_character(character):
                                results["synced"] += 1
                            else:
                                results["skipped"] += 1
                                
                        except Exception as e:
                            self.logger.error(f"Error processing trending character {char_data.get('id', 'unknown')}: {e}")
                            results["errors"] += 1
                
                # Rate limiting between pages
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error syncing trending page {page}: {e}")
                results["errors"] += 1
        
        self.logger.info(f"Trending sync completed: {results}")
        return results

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
                response_data = await self.fetch_data(current_variables, query)
                
                if not response_data or data_key not in response_data:
                    break
                
                page_data = response_data[data_key]
                if not page_data:
                    break
                
                # Handle different response structures
                if isinstance(page_data, dict):
                    # Structure like { data: [...], pageInfo: {...} }
                    if 'media' in page_data or 'characters' in page_data:
                        # AniList Page structure
                        items = page_data.get('media', []) or page_data.get('characters', [])
                        has_next = page_data.get('pageInfo', {}).get('hasNextPage', False)
                        all_data.append(page_data)  # Return the whole page data
                    else:
                        # Direct data structure
                        items = [page_data] if page_data else []
                        has_next = False
                        all_data.extend(items)
                elif isinstance(page_data, list):
                    # Direct list structure
                    items = page_data
                    has_next = len(items) == page_size
                    all_data.extend(items)
                else:
                    break
                
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

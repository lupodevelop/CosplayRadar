"""
Specialized fetcher for character data from AniList
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .anilist_fetcher import AniListFetcher
from ..models import Character, MediaType


class CharacterFetcher(AniListFetcher):
    """Fetcher for character data from AniList"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    async def fetch_popular_characters(
        self, 
        limit: int = 100, 
        max_pages: Optional[int] = None
    ) -> List[Character]:
        """Fetch popular characters by favourites count"""
        query = self.get_popular_characters_query()
        variables = {
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
            
            characters = []
            timestamp = datetime.now()
            
            for page_data in raw_data:
                if 'characters' not in page_data:
                    continue
                    
                for char_item in page_data['characters']:
                    try:
                        character_data = await self._process_character_data(char_item, timestamp)
                        characters.append(character_data)
                        
                        if len(characters) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing character {char_item.get('id', 'unknown')}: {e}")
                        continue
                
                if len(characters) >= limit:
                    break
            
            self.logger.info(f"Successfully fetched {len(characters)} popular characters")
            return characters[:limit]  # Ensure we don't exceed the limit
            
        except Exception as e:
            self.logger.error(f"Error fetching popular characters: {e}")
            raise
    
    async def fetch_character_by_id(self, character_id: int) -> Optional[Character]:
        """Fetch detailed information for a specific character"""
        query = self.get_character_query()
        variables = {
            'id': character_id,
            'perPage': 25  # Get more media for detailed view
        }
        
        try:
            response = await self._make_request(query, variables)
            
            if not response or 'Character' not in response:
                self.logger.warning(f"No character found with ID {character_id}")
                return None
            
            char_data = response['Character']
            timestamp = datetime.now()
            
            return await self._process_character_data(char_data, timestamp, detailed=True)
            
        except Exception as e:
            self.logger.error(f"Error fetching character {character_id}: {e}")
            raise
    
    async def fetch_characters_by_ids(self, character_ids: List[int]) -> List[Character]:
        """Fetch multiple characters by their IDs"""
        characters = []
        
        for char_id in character_ids:
            try:
                char_data = await self.fetch_character_by_id(char_id)
                if char_data:
                    characters.append(char_data)
            except Exception as e:
                self.logger.error(f"Error fetching character {char_id}: {e}")
                continue
        
        self.logger.info(f"Successfully fetched {len(characters)} out of {len(character_ids)} requested characters")
        return characters
    
    async def search_characters(
        self,
        search_term: str,
        limit: int = 50
    ) -> List[Character]:
        """Search for characters by name"""
        query = """
        query ($search: String, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                    perPage
                }
                characters(search: $search, sort: FAVOURITES_DESC) {
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
        
        variables = {
            'search': search_term,
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
            
            characters = []
            timestamp = datetime.now()
            
            for page_data in raw_data:
                if 'characters' not in page_data:
                    continue
                    
                for char_item in page_data['characters']:
                    try:
                        character_data = await self._process_character_data(char_item, timestamp)
                        characters.append(character_data)
                        
                        if len(characters) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing character {char_item.get('id', 'unknown')}: {e}")
                        continue
                
                if len(characters) >= limit:
                    break
            
            self.logger.info(f"Successfully found {len(characters)} characters matching '{search_term}'")
            return characters[:limit]
            
        except Exception as e:
            self.logger.error(f"Error searching characters for '{search_term}': {e}")
            raise
    
    async def fetch_characters_from_media(
        self,
        media_id: int,
        limit: int = 50
    ) -> List[Character]:
        """Fetch characters from a specific anime/manga"""
        query = """
        query ($id: Int, $page: Int, $perPage: Int) {
            Media(id: $id) {
                id
                title {
                    romaji
                    english
                    native
                }
                characters(page: $page, perPage: $perPage, sort: FAVOURITES_DESC) {
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
                            media(perPage: 5, sort: FAVOURITES_DESC) {
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
                    pageInfo {
                        hasNextPage
                        currentPage
                    }
                }
            }
        }
        """
        
        variables = {
            'id': media_id,
            'perPage': min(limit, 50)
        }
        
        try:
            raw_data = await self.fetch_with_pagination(
                query=query,
                variables=variables,
                data_key='Media',
                page_size=variables['perPage'],
                max_pages=(limit + 49) // 50
            )
            
            characters = []
            timestamp = datetime.now()
            
            for media_data in raw_data:
                if 'characters' not in media_data:
                    continue
                    
                for char_edge in media_data['characters'].get('edges', []):
                    try:
                        char_node = char_edge.get('node', {})
                        if not char_node:
                            continue
                        
                        # Add role and voice actor info to character data
                        char_node['current_role'] = char_edge.get('role')
                        char_node['current_voice_actors'] = char_edge.get('voiceActors', [])
                        
                        character_data = await self._process_character_data(char_node, timestamp)
                        characters.append(character_data)
                        
                        if len(characters) >= limit:
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error processing character from media {media_id}: {e}")
                        continue
                
                if len(characters) >= limit:
                    break
            
            self.logger.info(f"Successfully fetched {len(characters)} characters from media {media_id}")
            return characters[:limit]
            
        except Exception as e:
            self.logger.error(f"Error fetching characters from media {media_id}: {e}")
            raise
    
    async def _process_character_data(
        self, 
        char_item: Dict[str, Any], 
        timestamp: datetime,
        detailed: bool = False
    ) -> Character:
        """Process raw character data into Character object"""
        
        # Process media appearances
        media_appearances = []
        if 'media' in char_item and char_item['media']:
            media_edges = char_item['media'].get('edges', [])
            for media_edge in media_edges:
                media_node = media_edge.get('node', {})
                if media_node:
                    media_info = {
                        'media_id': media_node.get('id'),
                        'title': media_node.get('title', {}),
                        'type': media_node.get('type'),
                        'format': media_node.get('format'),
                        'average_score': media_node.get('averageScore'),
                        'popularity': media_node.get('popularity', 0),
                        'favourites': media_node.get('favourites', 0),
                        'trending': media_node.get('trending', 0),
                        'cover_image': media_node.get('coverImage', {}),
                        'role': media_edge.get('role'),
                        'voice_actors': [
                            {
                                'id': va.get('id'),
                                'name': va.get('name', {}).get('full')
                            }
                            for va in media_edge.get('voiceActors', [])
                        ]
                    }
                    media_appearances.append(media_info)
        
        # Handle current role info if available (from media-specific queries)
        current_role = char_item.get('current_role')
        current_voice_actors = char_item.get('current_voice_actors', [])
        
        # Process alternative names
        name_data = char_item.get('name', {})
        alternative_names = name_data.get('alternative', []) if name_data.get('alternative') else []
        
        character_data = Character(
            timestamp=timestamp,
            character_id=char_item.get('id'),
            name=name_data.get('full'),
            name_native=name_data.get('native'),
            alternative_names=alternative_names,
            image=char_item.get('image', {}),
            description=char_item.get('description'),
            gender=char_item.get('gender'),
            age=char_item.get('age'),
            favourites=char_item.get('favourites', 0),
            media_appearances=media_appearances,
            current_role=current_role,
            current_voice_actors=[
                {
                    'id': va.get('id'),
                    'name': va.get('name', {}).get('full')
                }
                for va in current_voice_actors
            ]
        )
        
        return character_data

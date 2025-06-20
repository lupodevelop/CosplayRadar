"""
General data processor for cleaning, transforming and enhancing AniList data
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import re
from ..models import (
    CharacterData, TrendingData, MediaData, HistoricalData,
    MediaType, AniListConfig
)


class DataProcessor:
    """Process and enhance raw AniList data"""
    
    def __init__(self, config: Optional[AniListConfig] = None):
        self.config = config or AniListConfig()
        self.logger = logging.getLogger(__name__)
    
    def clean_character_data(self, character: CharacterData) -> CharacterData:
        """Clean and enhance character data"""
        try:
            # Clean description - remove HTML tags and excessive whitespace
            if character.description:
                character.description = self._clean_description(character.description)
            
            # Normalize gender
            character.gender = self._normalize_gender(character.gender)
            
            # Clean alternative names
            if character.alternative_names:
                character.alternative_names = [
                    name.strip() for name in character.alternative_names 
                    if name and name.strip()
                ]
            
            # Validate and clean media appearances
            character.media_appearances = self._clean_media_appearances(character.media_appearances)
            
            # Add popularity tier
            character.popularity_tier = self._calculate_popularity_tier(character.favourites)
            
            return character
            
        except Exception as e:
            self.logger.error(f"Error cleaning character data {character.character_id}: {e}")
            return character
    
    def clean_media_data(self, media: TrendingData) -> TrendingData:
        """Clean and enhance media data"""
        try:
            # Clean description
            if media.description:
                media.description = self._clean_description(media.description)
            
            # Normalize titles
            media.title = self._clean_titles(media.title)
            
            # Clean genres
            if media.genres:
                media.genres = [genre.strip() for genre in media.genres if genre and genre.strip()]
            
            # Clean and validate tags
            if media.tags:
                media.tags = self._clean_tags(media.tags)
            
            # Add quality tier
            media.quality_tier = self._calculate_quality_tier(media.average_score)
            
            # Add popularity tier
            media.popularity_tier = self._calculate_popularity_tier(media.popularity)
            
            return media
            
        except Exception as e:
            self.logger.error(f"Error cleaning media data {media.media_id}: {e}")
            return media
    
    def deduplicate_characters(self, characters: List[CharacterData]) -> List[CharacterData]:
        """Remove duplicate characters based on ID"""
        seen_ids = set()
        unique_characters = []
        
        for character in characters:
            if character.character_id not in seen_ids:
                seen_ids.add(character.character_id)
                unique_characters.append(character)
            else:
                self.logger.debug(f"Duplicate character found: {character.character_id}")
        
        self.logger.info(f"Deduplicated {len(characters)} -> {len(unique_characters)} characters")
        return unique_characters
    
    def deduplicate_media(self, media_list: List[TrendingData]) -> List[TrendingData]:
        """Remove duplicate media based on ID"""
        seen_ids = set()
        unique_media = []
        
        for media in media_list:
            if media.media_id not in seen_ids:
                seen_ids.add(media.media_id)
                unique_media.append(media)
            else:
                self.logger.debug(f"Duplicate media found: {media.media_id}")
        
        self.logger.info(f"Deduplicated {len(media_list)} -> {len(unique_media)} media")
        return unique_media
    
    def merge_character_data(
        self,
        existing_character: CharacterData,
        new_character: CharacterData
    ) -> CharacterData:
        """Merge character data, keeping the most complete information"""
        try:
            # Use the most recent timestamp
            merged_character = existing_character if existing_character.timestamp > new_character.timestamp else new_character
            
            # Merge media appearances
            existing_media_ids = {m.get('media_id') for m in existing_character.media_appearances}
            new_media_appearances = [
                m for m in new_character.media_appearances 
                if m.get('media_id') not in existing_media_ids
            ]
            merged_character.media_appearances.extend(new_media_appearances)
            
            # Keep the higher favourites count
            merged_character.favourites = max(existing_character.favourites, new_character.favourites)
            
            # Merge alternative names
            all_alt_names = set(existing_character.alternative_names or [])
            all_alt_names.update(new_character.alternative_names or [])
            merged_character.alternative_names = list(all_alt_names)
            
            # Use the more complete description
            if not merged_character.description or len(new_character.description or '') > len(merged_character.description or ''):
                merged_character.description = new_character.description
            
            return merged_character
            
        except Exception as e:
            self.logger.error(f"Error merging character data {existing_character.character_id}: {e}")
            return existing_character
    
    def extract_character_relationships(
        self,
        characters: List[CharacterData]
    ) -> Dict[int, List[int]]:
        """Extract relationships between characters based on shared media"""
        relationships = {}
        
        # Create media -> characters mapping
        media_characters = {}
        for character in characters:
            for media_appearance in character.media_appearances:
                media_id = media_appearance.get('media_id')
                if media_id:
                    if media_id not in media_characters:
                        media_characters[media_id] = []
                    media_characters[media_id].append(character.character_id)
        
        # Extract relationships
        for character in characters:
            char_id = character.character_id
            relationships[char_id] = set()
            
            # Find characters that appear in the same media
            for media_appearance in character.media_appearances:
                media_id = media_appearance.get('media_id')
                if media_id in media_characters:
                    for related_char_id in media_characters[media_id]:
                        if related_char_id != char_id:
                            relationships[char_id].add(related_char_id)
            
            relationships[char_id] = list(relationships[char_id])
        
        self.logger.info(f"Extracted relationships for {len(relationships)} characters")
        return relationships
    
    def calculate_character_cosplay_potential(self, character: CharacterData) -> float:
        """Calculate cosplay potential score based on various factors"""
        try:
            score = 0.0
            
            # Base popularity factor (log scale)
            if character.favourites > 0:
                score += min(40, character.favourites / 100)
            
            # Gender factor (female characters often more popular for cosplay) 
            if character.gender == 'FEMALE':
                score += 15
            elif character.gender == 'MALE':
                score += 10
            
            # Media popularity factor
            media_score = 0
            for media in character.media_appearances:
                media_popularity = media.get('popularity', 0)
                media_score += min(5, media_popularity / 1000)
            score += min(20, media_score)
            
            # Role importance factor
            main_roles = sum(1 for m in character.media_appearances if m.get('role') == 'MAIN')
            score += min(15, main_roles * 3)
            
            # Recent media factor
            recent_media = self._count_recent_media_appearances(character)
            score += min(10, recent_media * 2)
            
            return min(100.0, max(0.0, score))
            
        except Exception as e:
            self.logger.error(f"Error calculating cosplay potential for {character.character_id}: {e}")
            return 0.0
    
    def filter_characters_by_criteria(
        self,
        characters: List[CharacterData],
        min_favourites: int = 0,
        gender_filter: Optional[str] = None,
        media_type_filter: Optional[MediaType] = None,
        max_age: Optional[int] = None
    ) -> List[CharacterData]:
        """Filter characters based on specified criteria"""
        filtered_characters = []
        
        for character in characters:
            # Favourites filter
            if character.favourites < min_favourites:
                continue
            
            # Gender filter
            if gender_filter and character.gender != gender_filter:
                continue
            
            # Age filter
            if max_age and character.age and character.age > max_age:
                continue
            
            # Media type filter
            if media_type_filter:
                has_media_type = any(
                    self._get_media_type(media.get('type')) == media_type_filter
                    for media in character.media_appearances
                )
                if not has_media_type:
                    continue
            
            filtered_characters.append(character)
        
        self.logger.info(f"Filtered {len(characters)} -> {len(filtered_characters)} characters")
        return filtered_characters
    
    def _clean_description(self, description: str) -> str:
        """Clean HTML tags and excessive whitespace from description"""
        if not description:
            return ""
        
        # Remove HTML tags
        clean_desc = re.sub(r'<[^>]+>', '', description)
        
        # Remove excessive whitespace
        clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
        
        # Remove common AniList markup
        clean_desc = re.sub(r'~!.*?!~', '', clean_desc)  # Spoiler tags
        clean_desc = re.sub(r'__.*?__', '', clean_desc)   # Underline tags
        
        return clean_desc
    
    def _normalize_gender(self, gender: Optional[str]) -> Optional[str]:
        """Normalize gender strings"""
        if not gender:
            return None
        
        gender_upper = gender.upper()
        if gender_upper in ['FEMALE', 'F', 'GIRL', 'WOMAN']:
            return 'FEMALE'
        elif gender_upper in ['MALE', 'M', 'BOY', 'MAN']:
            return 'MALE'
        elif gender_upper in ['NON_BINARY', 'NON-BINARY', 'NONBINARY', 'NB']:
            return 'NON_BINARY'
        else:
            return gender_upper
    
    def _clean_titles(self, title: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate title data"""
        if not title:
            return {}
        
        cleaned_title = {}
        for key, value in title.items():
            if value and isinstance(value, str):
                cleaned_title[key] = value.strip()
        
        return cleaned_title
    
    def _clean_media_appearances(self, media_appearances: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and validate media appearance data"""
        if not media_appearances:
            return []
        
        cleaned_appearances = []
        for media in media_appearances:
            if media.get('media_id'):
                cleaned_appearances.append(media)
        
        return cleaned_appearances
    
    def _clean_tags(self, tags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean and validate tag data"""
        if not tags:
            return []
        
        cleaned_tags = []
        for tag in tags:
            if tag.get('name') and tag.get('name').strip():
                cleaned_tag = {
                    'name': tag['name'].strip(),
                    'rank': tag.get('rank', 0)
                }
                if tag.get('category'):
                    cleaned_tag['category'] = tag['category']
                cleaned_tags.append(cleaned_tag)
        
        # Sort by rank descending
        cleaned_tags.sort(key=lambda x: x.get('rank', 0), reverse=True)
        
        return cleaned_tags
    
    def _calculate_popularity_tier(self, count: int) -> str:
        """Calculate popularity tier based on count"""
        if count >= 10000:
            return 'S'
        elif count >= 5000:
            return 'A'
        elif count >= 1000:
            return 'B'
        elif count >= 500:
            return 'C'
        else:
            return 'D'
    
    def _calculate_quality_tier(self, score: Optional[int]) -> str:
        """Calculate quality tier based on score"""
        if not score:
            return 'D'
        
        if score >= 90:
            return 'S'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'
    
    def _count_recent_media_appearances(self, character: CharacterData) -> int:
        """Count recent media appearances (last 2 years)"""
        current_year = datetime.now().year
        count = 0
        
        for media in character.media_appearances:
            season_year = media.get('season_year')
            if season_year and current_year - season_year <= 2:
                count += 1
        
        return count
    
    def _get_media_type(self, type_str: Optional[str]) -> Optional[MediaType]:
        """Convert string to MediaType enum"""
        if not type_str:
            return None
        
        if type_str.upper() == 'ANIME':
            return MediaType.ANIME
        elif type_str.upper() == 'MANGA':
            return MediaType.MANGA
        else:
            return None

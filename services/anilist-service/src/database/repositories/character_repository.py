"""
Character repository with upsert logic for sync operations
"""
import logging
from typing import List, Optional, Dict, Any, Tuple, Set
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func, select
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from datetime import datetime, timedelta

from ..models import Character, CharacterMedia, Media, TrendingSnapshot
from ...models import Character as PydanticCharacter, CharacterMedia as PydanticCharacterMedia


class CharacterRepository:
    """Repository for character data operations with upsert support"""
    
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    def upsert_character(self, character_data: PydanticCharacter) -> Tuple[Character, bool]:
        """
        Upsert character data (insert or update if exists)
        Returns (character, is_new) tuple
        """
        try:
            existing = self.get_character_by_id(character_data.id)
            
            if existing:
                # Update existing character
                is_updated = self._update_character_if_changed(existing, character_data)
                return existing, False
            else:
                # Create new character
                new_character = self._create_character_from_data(character_data)
                return new_character, True
                
        except Exception as e:
            self.logger.error(f"Error upserting character {character_data.id}: {e}")
            raise
    
    def upsert_characters_batch(self, characters_data: List[PydanticCharacter]) -> Dict[str, int]:
        """
        Batch upsert characters for better performance
        Returns stats: {'created': int, 'updated': int, 'skipped': int}
        """
        stats = {'created': 0, 'updated': 0, 'skipped': 0}
        
        try:
            # Get existing character IDs in batch
            character_ids = [char.id for char in characters_data]
            existing_chars = self._get_existing_characters_map(character_ids)
            
            # Process in batches
            batch_size = 100
            for i in range(0, len(characters_data), batch_size):
                batch = characters_data[i:i + batch_size]
                batch_stats = self._process_character_batch(batch, existing_chars)
                
                # Update stats
                for key in stats:
                    stats[key] += batch_stats[key]
                
                # Commit batch
                self.session.commit()
                
            self.logger.info(f"Batch upsert completed: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in batch upsert: {e}")
            self.session.rollback()
            raise
    
    def _process_character_batch(self, batch: List[PydanticCharacter], existing_chars: Dict[int, Character]) -> Dict[str, int]:
        """Process a batch of characters"""
        stats = {'created': 0, 'updated': 0, 'skipped': 0}
        
        for char_data in batch:
            try:
                if char_data.id in existing_chars:
                    # Update existing
                    existing = existing_chars[char_data.id]
                    if self._should_update_character(existing, char_data):
                        self._update_character_fields(existing, char_data)
                        stats['updated'] += 1
                    else:
                        stats['skipped'] += 1
                else:
                    # Create new
                    self._create_character_from_data(char_data)
                    stats['created'] += 1
                    
            except Exception as e:
                self.logger.warning(f"Error processing character {char_data.id}: {e}")
                stats['skipped'] += 1
                
        return stats
    
    def _get_existing_characters_map(self, character_ids: List[int]) -> Dict[int, Character]:
        """Get existing characters as a map for efficient lookup"""
        existing = self.session.query(Character).filter(
            Character.id.in_(character_ids)
        ).all()
        
        return {char.id: char for char in existing}
    
    def _should_update_character(self, existing: Character, new_data: PydanticCharacter) -> bool:
        """
        Determine if character should be updated based on data freshness and changes
        """
        # Always update if data is stale (older than configured threshold)
        if existing.updated_at:
            age_hours = (datetime.now() - existing.updated_at).total_seconds() / 3600
            if age_hours > 168:  # 7 days - from config
                return True
        
        # Update if significant changes in key metrics
        significant_fields = {
            'favourites': 0.05,  # 5% change threshold
            'trending': 0.1,     # 10% change threshold
        }
        
        for field, threshold in significant_fields.items():
            old_val = getattr(existing, field, 0) or 0
            new_val = getattr(new_data, field, 0) or 0
            
            if old_val > 0:
                change_ratio = abs(new_val - old_val) / old_val
                if change_ratio > threshold:
                    return True
        
        # Update if description changed significantly
        if existing.description != new_data.description:
            return True
            
        return False
    
    def _update_character_fields(self, existing: Character, new_data: PydanticCharacter):
        """Update character fields with new data"""
        # Always update these fields
        always_update = [
            'favourites', 'is_favourite', 'mod_notes'
        ]
        
        for field in always_update:
            if hasattr(new_data, field):
                setattr(existing, field, getattr(new_data, field))
        
        # Update other fields if they changed
        field_mappings = {
            'description': 'description',
            'gender': 'gender',
            'age': 'age',
            'blood_type': 'blood_type',
        }
        
        for new_field, db_field in field_mappings.items():
            new_val = getattr(new_data, new_field, None)
            if new_val is not None and getattr(existing, db_field) != new_val:
                setattr(existing, db_field, new_val)
        
        # Update image URLs
        if new_data.image:
            existing.image_large = new_data.image.large
            existing.image_medium = new_data.image.medium
        
        # Update name fields
        if new_data.name:
            existing.name_first = new_data.name.first
            existing.name_middle = new_data.name.middle
            existing.name_last = new_data.name.last
            existing.name_full = new_data.name.full
            existing.name_native = new_data.name.native
            existing.name_alternative = new_data.name.alternative or []
            existing.name_alternative_spoiler = new_data.name.alternative_spoiler or []
        
        # Update date of birth
        if new_data.date_of_birth:
            existing.birth_year = new_data.date_of_birth.year
            existing.birth_month = new_data.date_of_birth.month
            existing.birth_day = new_data.date_of_birth.day
        
        existing.updated_at = datetime.now()
    
    def _create_character_from_data(self, char_data: PydanticCharacter) -> Character:
        """Create new character from Pydantic model"""
        character = Character(
            id=char_data.id,
            name_first=char_data.name.first if char_data.name else None,
            name_middle=char_data.name.middle if char_data.name else None,
            name_last=char_data.name.last if char_data.name else None,
            name_full=char_data.name.full if char_data.name else None,
            name_native=char_data.name.native if char_data.name else None,
            name_alternative=char_data.name.alternative if char_data.name else [],
            name_alternative_spoiler=char_data.name.alternative_spoiler if char_data.name else [],
            image_large=char_data.image.large if char_data.image else None,
            image_medium=char_data.image.medium if char_data.image else None,
            description=char_data.description,
            gender=char_data.gender,
            age=char_data.age,
            blood_type=char_data.blood_type,
            birth_year=char_data.date_of_birth.year if char_data.date_of_birth else None,
            birth_month=char_data.date_of_birth.month if char_data.date_of_birth else None,
            birth_day=char_data.date_of_birth.day if char_data.date_of_birth else None,
            is_favourite=char_data.is_favourite,
            is_favourite_blocked=char_data.is_favourite_blocked,
            site_url=char_data.site_url,
            favourites=char_data.favourites,
            mod_notes=char_data.mod_notes,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.session.add(character)
        self.session.flush()  # Get the ID
        
        self.logger.debug(f"Created character {char_data.id}")
        return character
    
    def get_character_by_anilist_id(self, character_id: int) -> Optional[Character]:
        """Get character by AniList ID"""
        return self.session.query(Character).filter(
            Character.character_id == character_id
        ).first()
    
    def get_character_by_id(self, id: int) -> Optional[Character]:
        """Get character by database ID"""
        return self.session.query(Character).filter(Character.id == id).first()
    
    def get_characters_by_ids(self, character_ids: List[int]) -> List[Character]:
        """Get multiple characters by IDs"""
        return self.session.query(Character).filter(
            Character.id.in_(character_ids)
        ).all()
    
    def get_trending_characters(self, limit: int = 50, gender: str = None) -> List[Character]:
        """Get trending characters, optionally filtered by gender"""
        query = self.session.query(Character).join(TrendingSnapshot).filter(
            TrendingSnapshot.date >= datetime.now() - timedelta(days=1)
        )
        
        if gender:
            query = query.filter(Character.gender == gender)
        
        return query.order_by(desc(TrendingSnapshot.trending_score)).limit(limit).all()
    
    def get_characters_needing_update(self, max_age_hours: int = 168) -> List[Character]:
        """Get characters that need data refresh"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        return self.session.query(Character).filter(
            or_(
                Character.updated_at.is_(None),
                Character.updated_at < cutoff_time
            )
        ).all()
    
    def search_characters(self, query: str, limit: int = 20) -> List[Character]:
        """Search characters by name"""
        search_pattern = f"%{query}%"
        
        return self.session.query(Character).filter(
            or_(
                Character.name_full.ilike(search_pattern),
                Character.name_first.ilike(search_pattern),
                Character.name_last.ilike(search_pattern),
                Character.name_native.ilike(search_pattern)
            )
        ).order_by(desc(Character.favourites)).limit(limit).all()
    
    def get_character_stats(self) -> Dict[str, Any]:
        """Get character statistics"""
        total = self.session.query(Character).count()
        
        gender_stats = self.session.query(
            Character.gender,
            func.count(Character.id)
        ).group_by(Character.gender).all()
        
        return {
            'total_characters': total,
            'gender_distribution': dict(gender_stats),
            'avg_favourites': self.session.query(func.avg(Character.favourites)).scalar() or 0
        }
    
    def cleanup_old_characters(self, days_old: int = 365) -> int:
        """Remove characters not updated in X days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted = self.session.query(Character).filter(
            Character.updated_at < cutoff_date,
            Character.favourites < 10  # Only delete unpopular characters
        ).delete()
        
        return deleted
    
    def delete_character(self, character_id: int) -> bool:
        """Delete character by AniList ID"""
        try:
            character = self.get_character_by_anilist_id(character_id)
            if character:
                self.session.delete(character)
                self.logger.debug(f"Deleted character {character_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting character {character_id}: {e}")
            raise
    
    def _create_character_media_relations(
        self, 
        character: Character, 
        media_appearances: List[Dict[str, Any]]
    ):
        """Create character-media relationships"""
        for media_appearance in media_appearances:
            try:
                media_id = media_appearance.get('media_id')
                if not media_id:
                    continue
                
                # Find or create media record
                media = self.session.query(Media).filter(
                    Media.media_id == media_id
                ).first()
                
                if not media:
                    # Create minimal media record
                    media = Media(
                        media_id=media_id,
                        title_romaji=media_appearance.get('title', {}).get('romaji'),
                        title_english=media_appearance.get('title', {}).get('english'),
                        title_native=media_appearance.get('title', {}).get('native'),
                        media_type=self._get_media_type_enum(media_appearance.get('type')),
                        format=media_appearance.get('format'),
                        popularity=media_appearance.get('popularity', 0),
                        favourites=media_appearance.get('favourites', 0),
                        average_score=media_appearance.get('average_score'),
                        trending_rank=media_appearance.get('trending', 0)
                    )
                    self.session.add(media)
                    self.session.flush()
                
                # Create character-media relationship
                char_media = CharacterMedia(
                    character_id=character.id,
                    media_id=media.id,
                    role=media_appearance.get('role'),
                    voice_actors=media_appearance.get('voice_actors', []),
                    media_popularity=media_appearance.get('popularity', 0),
                    media_favourites=media_appearance.get('favourites', 0),
                    media_average_score=media_appearance.get('average_score'),
                    media_trending=media_appearance.get('trending', 0)
                )
                self.session.add(char_media)
                
            except Exception as e:
                self.logger.error(f"Error creating character-media relation: {e}")
                continue
    
    def _update_character_media_relations(
        self, 
        character: Character, 
        media_appearances: List[Dict[str, Any]]
    ):
        """Update character-media relationships"""
        # Get existing relationships
        existing_relations = {
            rel.media.media_id: rel for rel in character.media_appearances
        }
        
        # Process new appearances
        new_media_ids = set()
        for media_appearance in media_appearances:
            media_id = media_appearance.get('media_id')
            if not media_id:
                continue
            
            new_media_ids.add(media_id)
            
            if media_id in existing_relations:
                # Update existing relation
                rel = existing_relations[media_id]
                rel.role = media_appearance.get('role')
                rel.voice_actors = media_appearance.get('voice_actors', [])
                rel.media_popularity = media_appearance.get('popularity', 0)
                rel.media_favourites = media_appearance.get('favourites', 0)
                rel.media_average_score = media_appearance.get('average_score')
                rel.media_trending = media_appearance.get('trending', 0)
                rel.updated_at = datetime.utcnow()
            else:
                # Create new relation (similar to _create_character_media_relations)
                try:
                    media = self.session.query(Media).filter(
                        Media.media_id == media_id
                    ).first()
                    
                    if not media:
                        media = Media(
                            media_id=media_id,
                            title_romaji=media_appearance.get('title', {}).get('romaji'),
                            title_english=media_appearance.get('title', {}).get('english'),
                            title_native=media_appearance.get('title', {}).get('native'),
                            media_type=self._get_media_type_enum(media_appearance.get('type')),
                            format=media_appearance.get('format'),
                            popularity=media_appearance.get('popularity', 0),
                            favourites=media_appearance.get('favourites', 0),
                            average_score=media_appearance.get('average_score'),
                            trending_rank=media_appearance.get('trending', 0)
                        )
                        self.session.add(media)
                        self.session.flush()
                    
                    char_media = CharacterMedia(
                        character_id=character.id,
                        media_id=media.id,
                        role=media_appearance.get('role'),
                        voice_actors=media_appearance.get('voice_actors', []),
                        media_popularity=media_appearance.get('popularity', 0),
                        media_favourites=media_appearance.get('favourites', 0),
                        media_average_score=media_appearance.get('average_score'),
                        media_trending=media_appearance.get('trending', 0)
                    )
                    self.session.add(char_media)
                    
                except Exception as e:
                    self.logger.error(f"Error creating new character-media relation: {e}")
                    continue
        
        # Remove relations that are no longer present
        for media_id, rel in existing_relations.items():
            if media_id not in new_media_ids:
                self.session.delete(rel)
    
    def _get_media_type_enum(self, media_type_str: str):
        """Convert string to MediaTypeEnum"""
        from ..models import MediaTypeEnum
        
        if media_type_str == 'ANIME':
            return MediaTypeEnum.ANIME
        elif media_type_str == 'MANGA':
            return MediaTypeEnum.MANGA
        else:
            return MediaTypeEnum.ANIME  # Default

"""
Repository per AniListCharacter con nuovo schema estensibile
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, select
from datetime import datetime, timedelta, date

from ..schema import AniListCharacter, AniListMedia, AniListCharacterMedia, AniListTrendingSnapshot
from ...models import Character as PydanticCharacter, CharacterMedia as PydanticCharacterMedia


class AniListCharacterRepository:
    """Repository per operazioni sui personaggi AniList"""
    
    def __init__(self, session: Session):
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    def upsert_character(self, character_data: PydanticCharacter) -> Tuple[AniListCharacter, bool]:
        """
        Upsert character data - inserisce nuovo o aggiorna esistente
        Returns (character, is_new) tuple
        """
        try:
            existing = self.get_character_by_id(character_data.id)
            
            if existing:
                # Aggiorna personaggio esistente se necessario
                if self._should_update_character(existing, character_data):
                    self._update_character_fields(existing, character_data)
                    return existing, False
                else:
                    return existing, False
            else:
                # Crea nuovo personaggio
                new_character = self._create_character_from_data(character_data)
                return new_character, True
                
        except Exception as e:
            self.logger.error(f"Error upserting character {character_data.id}: {e}")
            raise
    
    def upsert_characters_batch(self, characters_data: List[PydanticCharacter]) -> Dict[str, int]:
        """
        Batch upsert per migliore performance
        Returns stats: {'created': int, 'updated': int, 'skipped': int}
        """
        stats = {'created': 0, 'updated': 0, 'skipped': 0}
        
        try:
            # Ottieni mappa personaggi esistenti
            character_ids = [char.id for char in characters_data]
            existing_chars = self._get_existing_characters_map(character_ids)
            
            # Processa in batch
            batch_size = 100
            for i in range(0, len(characters_data), batch_size):
                batch = characters_data[i:i + batch_size]
                batch_stats = self._process_character_batch(batch, existing_chars)
                
                # Aggiorna statistiche
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
    
    def _process_character_batch(self, batch: List[PydanticCharacter], existing_chars: Dict[int, AniListCharacter]) -> Dict[str, int]:
        """Processa un batch di personaggi"""
        stats = {'created': 0, 'updated': 0, 'skipped': 0}
        
        for char_data in batch:
            try:
                if char_data.id in existing_chars:
                    # Aggiorna esistente
                    existing = existing_chars[char_data.id]
                    if self._should_update_character(existing, char_data):
                        self._update_character_fields(existing, char_data)
                        stats['updated'] += 1
                    else:
                        stats['skipped'] += 1
                else:
                    # Crea nuovo
                    self._create_character_from_data(char_data)
                    stats['created'] += 1
                    
            except Exception as e:
                self.logger.warning(f"Error processing character {char_data.id}: {e}")
                stats['skipped'] += 1
                
        return stats
    
    def _get_existing_characters_map(self, character_ids: List[int]) -> Dict[int, AniListCharacter]:
        """Ottieni personaggi esistenti come mappa"""
        existing = self.session.query(AniListCharacter).filter(
            AniListCharacter.id.in_(character_ids)
        ).all()
        
        return {char.id: char for char in existing}
    
    def _should_update_character(self, existing: AniListCharacter, new_data: PydanticCharacter) -> bool:
        """
        Determina se il personaggio deve essere aggiornato
        """
        # Aggiorna sempre se i dati sono vecchi (più di 7 giorni)
        if existing.updated_at:
            age_hours = (datetime.now() - existing.updated_at).total_seconds() / 3600
            if age_hours > 168:  # 7 giorni
                return True
        
        # Aggiorna se cambio significativo in favourites (>5%)
        if existing.favourites and new_data.favourites:
            change_ratio = abs(new_data.favourites - existing.favourites) / existing.favourites
            if change_ratio > 0.05:  # 5% soglia
                return True
        
        # Aggiorna se descrizione cambiata
        if existing.description != new_data.description:
            return True
            
        return False
    
    def _update_character_fields(self, existing: AniListCharacter, new_data: PydanticCharacter):
        """Aggiorna campi del personaggio"""
        # Campi sempre aggiornati
        existing.favourites = new_data.favourites
        existing.is_favourite = getattr(new_data, 'is_favourite', False)
        existing.is_favourite_blocked = getattr(new_data, 'is_favourite_blocked', False)
        existing.mod_notes = getattr(new_data, 'mod_notes', None)
        
        # Altri campi se cambiati
        if new_data.description:
            existing.description = new_data.description
        if new_data.gender:
            existing.gender = new_data.gender
        if new_data.age:
            existing.age = new_data.age
        if new_data.blood_type:
            existing.blood_type = new_data.blood_type
        
        # Immagini
        if new_data.image:
            existing.image_large = str(new_data.image.large) if new_data.image and new_data.image.large else None
            existing.image_medium = str(new_data.image.medium) if new_data.image and new_data.image.medium else None
        
        # Nome
        if new_data.name:
            existing.name_first = new_data.name.first
            existing.name_middle = new_data.name.middle
            existing.name_last = new_data.name.last
            existing.name_full = new_data.name.full
            existing.name_native = new_data.name.native
            existing.name_alternative = new_data.name.alternative or []
            existing.name_alternative_spoiler = getattr(new_data.name, 'alternative_spoiler', []) if new_data.name else []
        
        # Data di nascita
        if new_data.date_of_birth:
            existing.birth_year = new_data.date_of_birth.year
            existing.birth_month = new_data.date_of_birth.month
            existing.birth_day = new_data.date_of_birth.day
        
        existing.last_fetched_at = datetime.now()
    
    def _create_character_from_data(self, char_data: PydanticCharacter) -> AniListCharacter:
        """Crea nuovo personaggio dai dati Pydantic"""
        character = AniListCharacter(
            id=char_data.id,
            name_first=char_data.name.first if char_data.name else None,
            name_middle=char_data.name.middle if char_data.name else None,
            name_last=char_data.name.last if char_data.name else None,
            name_full=char_data.name.full if char_data.name else None,
            name_native=char_data.name.native if char_data.name else None,
            name_alternative=char_data.name.alternative if char_data.name else [],
            name_alternative_spoiler=getattr(char_data.name, 'alternative_spoiler', []) if char_data.name else [],
            image_large=str(char_data.image.large) if char_data.image and char_data.image.large else None,
            image_medium=str(char_data.image.medium) if char_data.image and char_data.image.medium else None,
            description=char_data.description,
            gender=char_data.gender,
            age=char_data.age,
            blood_type=char_data.blood_type,
            birth_year=char_data.date_of_birth.year if char_data.date_of_birth else None,
            birth_month=char_data.date_of_birth.month if char_data.date_of_birth else None,
            birth_day=char_data.date_of_birth.day if char_data.date_of_birth else None,
            is_favourite=getattr(char_data, 'is_favourite', False),
            is_favourite_blocked=getattr(char_data, 'is_favourite_blocked', False),
            site_url=getattr(char_data, 'site_url', None),
            favourites=char_data.favourites,
            mod_notes=getattr(char_data, 'mod_notes', None),
            last_fetched_at=datetime.now()
        )
        
        self.session.add(character)
        self.session.flush()  # Ottieni ID
        
        return character
    
    # Query methods
    
    def get_character_by_id(self, character_id: int) -> Optional[AniListCharacter]:
        """Ottieni personaggio per ID AniList"""
        return self.session.query(AniListCharacter).filter(
            AniListCharacter.id == character_id
        ).first()
    
    def get_characters_by_ids(self, character_ids: List[int]) -> List[AniListCharacter]:
        """Ottieni multipli personaggi per ID"""
        return self.session.query(AniListCharacter).filter(
            AniListCharacter.id.in_(character_ids)
        ).all()
    
    def get_trending_characters(self, limit: int = 50, gender: str = None, days: int = 7) -> List[AniListCharacter]:
        """
        Ottieni personaggi trending
        NOTA: Per ora ordina per favourites dato che non abbiamo ancora calcolato i trending scores
        """
        query = self.session.query(AniListCharacter)
        
        if gender:
            query = query.filter(AniListCharacter.gender == gender)
        
        # Per ora ordiniamo per favourites come proxy del trending
        # TODO: Implementare il calcolo del trending score basato su:
        # - Favourites crescita
        # - Media associati trending  
        # - Recency factor
        # - Gender boost
        return query.order_by(desc(AniListCharacter.favourites)).limit(limit).all()
    
    def get_characters_needing_update(self, max_age_hours: int = 168) -> List[AniListCharacter]:
        """Ottieni personaggi che necessitano aggiornamento"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        return self.session.query(AniListCharacter).filter(
            or_(
                AniListCharacter.last_fetched_at.is_(None),
                AniListCharacter.last_fetched_at < cutoff_time
            )
        ).all()
    
    def search_characters(self, query: str, limit: int = 20) -> List[AniListCharacter]:
        """Cerca personaggi per nome"""
        search_pattern = f"%{query}%"
        
        return self.session.query(AniListCharacter).filter(
            or_(
                AniListCharacter.name_full.ilike(search_pattern),
                AniListCharacter.name_first.ilike(search_pattern),
                AniListCharacter.name_last.ilike(search_pattern),
                AniListCharacter.name_native.ilike(search_pattern)
            )
        ).order_by(desc(AniListCharacter.favourites)).limit(limit).all()
    
    def get_character_stats(self) -> Dict[str, Any]:
        """Ottieni statistiche personaggi"""
        total = self.session.query(AniListCharacter).count()
        
        gender_stats = self.session.query(
            AniListCharacter.gender,
            func.count(AniListCharacter.id)
        ).group_by(AniListCharacter.gender).all()
        
        avg_favourites = self.session.query(func.avg(AniListCharacter.favourites)).scalar() or 0
        
        return {
            'total_characters': total,
            'gender_distribution': dict(gender_stats),
            'avg_favourites': float(avg_favourites),
            'last_update': self.session.query(func.max(AniListCharacter.updated_at)).scalar()
        }
    
    def cleanup_old_characters(self, days_old: int = 365) -> int:
        """Rimuovi personaggi non aggiornati da X giorni (solo se poco popolari)"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted = self.session.query(AniListCharacter).filter(
            AniListCharacter.updated_at < cutoff_date,
            AniListCharacter.favourites < 10  # Solo personaggi non popolari
        ).delete()
        
        return deleted
    
    def create_trending_snapshot(self, character_id: int, trending_data: Dict[str, Any]) -> AniListTrendingSnapshot:
        """Crea snapshot trending per personaggio"""
        
        # Ottieni dati personaggio per denormalizzazione
        character = self.get_character_by_id(character_id)
        
        snapshot = AniListTrendingSnapshot(
            character_id=character_id,
            entity_type='character',
            snapshot_date=trending_data.get('date', date.today()),
            period_type=trending_data.get('period_type', 'daily'),
            anilist_rank=trending_data.get('anilist_rank'),
            anilist_trending_score=trending_data.get('anilist_trending_score', 0),
            calculated_trending_score=trending_data['calculated_trending_score'],
            base_score=trending_data['base_score'],
            gender_boost=trending_data.get('gender_boost', 1.0),
            recency_boost=trending_data.get('recency_boost', 1.0),
            quality_boost=trending_data.get('quality_boost', 1.0),
            role_weight=trending_data.get('role_weight', 1.0),
            total_boost_multiplier=trending_data.get('total_boost_multiplier', 1.0),
            algorithm_version=trending_data.get('algorithm_version', '1.0'),
            calculation_metadata=trending_data.get('metadata'),
            # Dati denormalizzati
            character_name=character.name_full if character else None,
            character_gender=character.gender if character else None,
            character_favourites=character.favourites if character else None,
            character_image=character.image_large if character else None,
        )
        
        self.session.add(snapshot)
        return snapshot

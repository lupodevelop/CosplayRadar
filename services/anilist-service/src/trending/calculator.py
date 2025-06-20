"""
Trending Score Calculator
Implementa l'algoritmo di calcolo del trending score per personaggi AniList
"""
import json
import logging
import math
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..database.schema import (
    AniListCharacter, 
    CharacterFavouritesHistory, 
    TrendingConfig,
    AniListTrendingSnapshot,
    AniListCharacterMedia
)
from ..models import ServiceConfig


class TrendingScoreCalculator:
    """Calcola il trending score per i personaggi AniList"""
    
    def __init__(self, session: Session, config: Optional[ServiceConfig] = None):
        self.session = session
        self.config = config or ServiceConfig()
        self.logger = logging.getLogger(__name__)
        
        # Carica configurazione trending
        self.trending_config = self._load_trending_config()
        
    def _load_trending_config(self) -> Dict[str, Any]:
        """Carica configurazione trending da file JSON o database"""
        try:
            # Prima prova a caricare da file JSON
            config_path = Path(__file__).parent.parent.parent / "config" / "trending_config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            
            # Fallback: carica da database (se implementato)
            self.logger.warning("File configurazione trending non trovato, uso valori default")
            return self._get_default_config()
            
        except Exception as e:
            self.logger.error(f"Errore caricamento configurazione trending: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configurazione di default per il trending"""
        return {
            "gender_boosts": {"FEMALE": 1.4, "MALE": 1.0, "NON_BINARY": 1.2, "unknown": 0.95},
            "role_boosts": {"MAIN": 1.0, "SUPPORTING": 1.3, "BACKGROUND": 1.5},
            "series_status_boosts": {
                "RELEASING_NEW": 2.5, "RELEASING_CURRENT": 1.8, "RELEASING_LONG": 1.2,
                "FINISHED_RECENT": 1.5, "FINISHED_SEMI_RECENT": 1.1, "FINISHED_OLD": 0.9,
                "NOT_YET_RELEASED": 1.3, "CANCELLED": 0.7, "HIATUS": 0.7,
                "releasing_new_days": 30, "releasing_current_days": 365,
                "finished_recent_days": 90, "finished_semi_recent_days": 365
            },
            "growth_calculation": {
                "weight_7_days": 0.5, "weight_30_days": 0.3, "weight_90_days": 0.2,
                "max_multiplier": 5.0, "min_multiplier": 0.1
            },
            "recency_factors": {
                "fresh_days": 7, "recent_days": 30, "semi_old_days": 90,
                "fresh_factor": 1.0, "recent_factor": 0.95, "semi_old_factor": 0.85, "old_factor": 0.7
            },
            "base_score": {"log_base": 10, "multiplier": 100, "min_favourites": 1}
        }
    
    def calculate_base_score(self, favourites: int) -> float:
        """Calcola il punteggio base usando il logaritmo"""
        config = self.trending_config["base_score"]
        min_fav = config["min_favourites"]
        adjusted_favourites = max(favourites, min_fav)
        
        return math.log10(adjusted_favourites + 1) * config["multiplier"]
    
    def calculate_growth_multiplier(self, character_id: int) -> float:
        """Calcola il moltiplicatore basato sulla crescita dei favourites"""
        try:
            now = datetime.now()
            growth_config = self.trending_config["growth_calculation"]
            
            # Ottieni favourites storici
            history_points = {
                7: now - timedelta(days=7),
                30: now - timedelta(days=30),
                90: now - timedelta(days=90)
            }
            
            current_favourites = self._get_current_favourites(character_id)
            if not current_favourites:
                return 1.0
            
            growth_components = []
            
            for days, date_threshold in history_points.items():
                historical_favs = self._get_historical_favourites(character_id, date_threshold)
                
                if historical_favs and historical_favs > 0:
                    growth_rate = (current_favourites - historical_favs) / historical_favs
                    weight = growth_config[f"weight_{days}_days"]
                    growth_components.append(growth_rate * weight)
                else:
                    # Se non ci sono dati storici, assume crescita neutrale
                    growth_components.append(0)
            
            # Calcola moltiplicatore finale
            total_growth = sum(growth_components)
            multiplier = 1 + total_growth
            
            # Applica limiti
            max_mult = growth_config["max_multiplier"]
            min_mult = growth_config["min_multiplier"]
            
            return max(min_mult, min(max_mult, multiplier))
            
        except Exception as e:
            self.logger.error(f"Errore calcolo crescita per character {character_id}: {e}")
            return 1.0
    
    def calculate_series_boost(self, character: AniListCharacter) -> float:
        """Calcola boost basato sulle serie associate"""
        try:
            if not character.media_appearances:
                return 1.0
            
            boosts = []
            weights = []
            
            for media_appearance in character.media_appearances:
                media = media_appearance.media
                role = media_appearance.character_role
                
                # Boost basato su status serie
                series_boost = self._get_series_status_boost(media)
                
                # Peso basato sul ruolo
                role_weight = self._get_role_weight(role)
                
                boosts.append(series_boost)
                weights.append(role_weight)
            
            if not boosts:
                return 1.0
            
            # Media pesata
            weighted_sum = sum(boost * weight for boost, weight in zip(boosts, weights))
            total_weight = sum(weights)
            
            return weighted_sum / total_weight if total_weight > 0 else 1.0
            
        except Exception as e:
            self.logger.error(f"Errore calcolo series boost per character {character.id}: {e}")
            return 1.0
    
    def _get_series_status_boost(self, media) -> float:
        """Calcola boost basato su status e data della serie"""
        try:
            config = self.trending_config["series_status_boosts"]
            status = media.status
            
            if status == "RELEASING":
                return self._get_releasing_boost(media, config)
            elif status == "FINISHED":
                return self._get_finished_boost(media, config)
            elif status == "NOT_YET_RELEASED":
                return config["NOT_YET_RELEASED"]
            elif status in ["CANCELLED", "HIATUS"]:
                return config.get(status, config["CANCELLED"])
            else:
                return 1.0
                
        except Exception as e:
            self.logger.error(f"Errore calcolo series status boost: {e}")
            return 1.0
    
    def _get_releasing_boost(self, media, config: Dict) -> float:
        """Calcola boost per serie in corso"""
        if not media.start_date_year:
            return config["RELEASING_CURRENT"]
        
        # Calcola giorni dall'inizio
        try:
            start_date = date(
                media.start_date_year,
                media.start_date_month or 1,
                media.start_date_day or 1
            )
            
            days_since_start = (date.today() - start_date).days
            
            if days_since_start <= config["releasing_new_days"]:
                return config["RELEASING_NEW"]
            elif days_since_start <= config["releasing_current_days"]:
                return config["RELEASING_CURRENT"]
            else:
                return config["RELEASING_LONG"]
                
        except Exception:
            return config["RELEASING_CURRENT"]
    
    def _get_finished_boost(self, media, config: Dict) -> float:
        """Calcola boost per serie concluse"""
        if not media.end_date_year:
            return config["FINISHED_SEMI_RECENT"]
        
        try:
            end_date = date(
                media.end_date_year,
                media.end_date_month or 12,
                media.end_date_day or 31
            )
            
            days_since_end = (date.today() - end_date).days
            
            if days_since_end <= config["finished_recent_days"]:
                return config["FINISHED_RECENT"]
            elif days_since_end <= config["finished_semi_recent_days"]:
                return config["FINISHED_SEMI_RECENT"]
            else:
                return config["FINISHED_OLD"]
                
        except Exception:
            return config["FINISHED_SEMI_RECENT"]
    
    def _get_role_weight(self, role: str) -> float:
        """Peso basato sul ruolo del personaggio"""
        weights = {"MAIN": 1.0, "SUPPORTING": 0.7, "BACKGROUND": 0.3}
        return weights.get(role, 0.5)
    
    def calculate_gender_boost(self, gender: Optional[str]) -> float:
        """Calcola boost basato sul genere"""
        config = self.trending_config["gender_boosts"]
        return config.get(gender or "unknown", config["unknown"])
    
    def calculate_role_boost(self, character: AniListCharacter) -> float:
        """Calcola boost basato sul ruolo principale"""
        if not character.media_appearances:
            return 1.0
        
        config = self.trending_config["role_boosts"]
        
        # Trova il ruolo più importante
        roles = [appearance.character_role for appearance in character.media_appearances]
        
        if "MAIN" in roles:
            return config["MAIN"]
        elif "SUPPORTING" in roles:
            return config["SUPPORTING"]
        else:
            return config["BACKGROUND"]
    
    def calculate_recency_factor(self, last_fetched_at: Optional[datetime]) -> float:
        """Calcola fattore di recency basato sull'ultimo aggiornamento"""
        if not last_fetched_at:
            return 0.7  # Penalità per dati mai aggiornati
        
        config = self.trending_config["recency_factors"]
        days_old = (datetime.now() - last_fetched_at).days
        
        if days_old <= config["fresh_days"]:
            return config["fresh_factor"]
        elif days_old <= config["recent_days"]:
            return config["recent_factor"]
        elif days_old <= config["semi_old_days"]:
            return config["semi_old_factor"]
        else:
            return config["old_factor"]
    
    def calculate_trending_score(self, character: AniListCharacter) -> Tuple[float, Dict[str, float]]:
        """
        Calcola il trending score completo per un personaggio
        
        Returns:
            Tuple[float, Dict]: (trending_score, components_dict)
        """
        try:
            # Calcola tutti i componenti
            base_score = self.calculate_base_score(character.favourites)
            growth_multiplier = self.calculate_growth_multiplier(character.id)
            series_boost = self.calculate_series_boost(character)
            gender_boost = self.calculate_gender_boost(character.gender)
            role_boost = self.calculate_role_boost(character)
            recency_factor = self.calculate_recency_factor(character.last_fetched_at)
            
            # Formula finale
            trending_score = (
                base_score * 
                growth_multiplier * 
                series_boost * 
                gender_boost * 
                role_boost * 
                recency_factor
            )
            
            # Componenti per debugging
            components = {
                "base_score": base_score,
                "growth_multiplier": growth_multiplier,
                "series_boost": series_boost,
                "gender_boost": gender_boost,
                "role_boost": role_boost,
                "recency_factor": recency_factor,
                "final_score": trending_score
            }
            
            return trending_score, components
            
        except Exception as e:
            self.logger.error(f"Errore calcolo trending score per character {character.id}: {e}")
            # Fallback su base score semplice
            base_score = self.calculate_base_score(character.favourites)
            return base_score, {"base_score": base_score, "error": str(e)}
    
    def _get_current_favourites(self, character_id: int) -> Optional[int]:
        """Ottieni favourites attuali del personaggio"""
        character = self.session.query(AniListCharacter).filter_by(id=character_id).first()
        return character.favourites if character else None
    
    def _get_historical_favourites(self, character_id: int, date_threshold: datetime) -> Optional[int]:
        """Ottieni favourites storici più vicini alla data specificata"""
        history = self.session.query(CharacterFavouritesHistory).filter(
            and_(
                CharacterFavouritesHistory.character_id == character_id,
                CharacterFavouritesHistory.recorded_at <= date_threshold
            )
        ).order_by(desc(CharacterFavouritesHistory.recorded_at)).first()
        
        return history.favourites if history else None
    
    def save_trending_snapshot(self, character: AniListCharacter, trending_score: float, 
                              components: Dict[str, float]) -> None:
        """Salva uno snapshot del trending score"""
        try:
            snapshot = AniListTrendingSnapshot(
                character_id=character.id,
                entity_type='character',
                snapshot_date=date.today(),
                period_type='daily',
                calculated_trending_score=trending_score,
                base_score=components.get('base_score'),
                growth_multiplier=components.get('growth_multiplier'),
                series_boost=components.get('series_boost'),
                gender_boost=components.get('gender_boost'),
                role_boost=components.get('role_boost'),
                recency_factor=components.get('recency_factor'),
                calculation_metadata=components,
                character_name=character.name_full or character.name_first,
                character_gender=character.gender,
                character_favourites=character.favourites,
                character_image=character.image_large
            )
            
            self.session.add(snapshot)
            
        except Exception as e:
            self.logger.error(f"Errore salvataggio snapshot per character {character.id}: {e}")
            raise
    
    def record_favourites_history(self, character: AniListCharacter) -> None:
        """Registra i favourites attuali nello storico"""
        try:
            history = CharacterFavouritesHistory(
                character_id=character.id,
                favourites=character.favourites,
                recorded_at=datetime.now()
            )
            
            self.session.add(history)
            
        except Exception as e:
            self.logger.error(f"Errore registrazione favourites history per character {character.id}: {e}")
            raise

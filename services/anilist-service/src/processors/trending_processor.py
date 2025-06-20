"""
Trending score processor with gender boost, recency boost, quality boost, and role weight
"""
import logging
import math
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..models import (
    CharacterData, TrendingData, MediaData, HistoricalData,
    TrendingScoreData, MediaType, AniListConfig
)


class TrendingProcessor:
    """Calculate trending scores using multiple factors and boosts"""
    
    def __init__(self, config: Optional[AniListConfig] = None):
        self.config = config or AniListConfig()
        self.logger = logging.getLogger(__name__)
        
        # Boost weights from config
        self.gender_boost_weight = self.config.gender_boost_weight
        self.recency_boost_weight = self.config.recency_boost_weight
        self.quality_boost_weight = self.config.quality_boost_weight
        self.role_weight_factor = self.config.role_weight_factor
        
        # Decay factors
        self.popularity_decay = 0.8
        self.favourites_decay = 0.7
        self.trending_decay = 0.9
        
        # Gender boost preferences
        self.gender_boosts = {
            'FEMALE': self.config.female_boost,
            'MALE': self.config.male_boost,
            'NON_BINARY': 1.0,
            None: 1.0  # Unknown gender
        }
        
        # Role weights
        self.role_weights = {
            'MAIN': 1.0,
            'SUPPORTING': 0.7,
            'BACKGROUND': 0.3,
            None: 0.5  # Unknown role
        }
    
    def calculate_character_trending_score(
        self,
        character: CharacterData,
        related_media: List[TrendingData] = None,
        historical_data: List[HistoricalData] = None
    ) -> TrendingScoreData:
        """Calculate comprehensive trending score for a character"""
        
        try:
            # Base metrics
            base_score = self._calculate_base_character_score(character)
            
            # Apply boosts
            gender_boost = self._calculate_gender_boost(character.gender)
            recency_boost = self._calculate_character_recency_boost(character, related_media)
            quality_boost = self._calculate_character_quality_boost(character, related_media)
            role_boost = self._calculate_role_boost(character)
            
            # Historical momentum (if available)
            momentum_boost = self._calculate_historical_momentum(historical_data) if historical_data else 1.0
            
            # Final trending score calculation
            trending_score = (
                base_score * 
                gender_boost * 
                recency_boost * 
                quality_boost * 
                role_boost * 
                momentum_boost
            )
            
            # Normalization (0-100 scale)
            normalized_score = min(100.0, max(0.0, trending_score))
            
            score_data = TrendingScoreData(
                entity_id=character.character_id,
                entity_type='character',
                timestamp=datetime.now(),
                base_score=base_score,
                gender_boost=gender_boost,
                recency_boost=recency_boost,
                quality_boost=quality_boost,
                role_boost=role_boost,
                momentum_boost=momentum_boost,
                final_score=normalized_score,
                calculation_details={
                    'favourites': character.favourites,
                    'gender': character.gender,
                    'media_count': len(character.media_appearances),
                    'main_roles': sum(1 for m in character.media_appearances if m.get('role') == 'MAIN'),
                    'avg_media_score': self._get_average_media_score(character.media_appearances),
                    'recent_media_count': self._count_recent_media(character.media_appearances)
                }
            )
            
            self.logger.debug(f"Character {character.character_id} trending score: {normalized_score:.2f}")
            return score_data
            
        except Exception as e:
            self.logger.error(f"Error calculating trending score for character {character.character_id}: {e}")
            # Return minimal score on error
            return TrendingScoreData(
                entity_id=character.character_id,
                entity_type='character',
                timestamp=datetime.now(),
                base_score=0.0,
                gender_boost=1.0,
                recency_boost=1.0,
                quality_boost=1.0,
                role_boost=1.0,
                momentum_boost=1.0,
                final_score=0.0,
                calculation_details={'error': str(e)}
            )
    
    def calculate_media_trending_score(
        self,
        media: TrendingData,
        historical_data: List[HistoricalData] = None
    ) -> TrendingScoreData:
        """Calculate comprehensive trending score for media"""
        
        try:
            # Base metrics
            base_score = self._calculate_base_media_score(media)
            
            # Apply boosts
            recency_boost = self._calculate_media_recency_boost(media)
            quality_boost = self._calculate_media_quality_boost(media)
            character_diversity_boost = self._calculate_character_diversity_boost(media)
            
            # Historical momentum
            momentum_boost = self._calculate_historical_momentum(historical_data) if historical_data else 1.0
            
            # Final trending score calculation
            trending_score = (
                base_score * 
                recency_boost * 
                quality_boost * 
                character_diversity_boost * 
                momentum_boost
            )
            
            # Normalization (0-100 scale)
            normalized_score = min(100.0, max(0.0, trending_score))
            
            score_data = TrendingScoreData(
                entity_id=media.media_id,
                entity_type='media',
                timestamp=datetime.now(),
                base_score=base_score,
                gender_boost=1.0,  # Not applicable for media
                recency_boost=recency_boost,
                quality_boost=quality_boost,
                role_boost=character_diversity_boost,  # Using this field for character diversity
                momentum_boost=momentum_boost,
                final_score=normalized_score,
                calculation_details={
                    'popularity': media.popularity,
                    'favourites': media.favourites,
                    'trending_rank': media.trending_rank,
                    'average_score': media.average_score,
                    'character_count': len(media.characters),
                    'main_character_count': sum(1 for c in media.characters if c.get('role') == 'MAIN'),
                    'season': media.season,
                    'season_year': media.season_year
                }
            )
            
            self.logger.debug(f"Media {media.media_id} trending score: {normalized_score:.2f}")
            return score_data
            
        except Exception as e:
            self.logger.error(f"Error calculating trending score for media {media.media_id}: {e}")
            return TrendingScoreData(
                entity_id=media.media_id,
                entity_type='media',
                timestamp=datetime.now(),
                base_score=0.0,
                gender_boost=1.0,
                recency_boost=1.0,
                quality_boost=1.0,
                role_boost=1.0,
                momentum_boost=1.0,
                final_score=0.0,
                calculation_details={'error': str(e)}
            )
    
    def batch_calculate_character_scores(
        self,
        characters: List[CharacterData],
        media_context: List[TrendingData] = None
    ) -> List[TrendingScoreData]:
        """Calculate trending scores for multiple characters efficiently"""
        
        scores = []
        media_lookup = {}
        
        # Create media lookup for efficiency
        if media_context:
            media_lookup = {media.media_id: media for media in media_context}
        
        for character in characters:
            try:
                # Find related media from context
                related_media = []
                for media_appearance in character.media_appearances:
                    media_id = media_appearance.get('media_id')
                    if media_id in media_lookup:
                        related_media.append(media_lookup[media_id])
                
                score = self.calculate_character_trending_score(character, related_media)
                scores.append(score)
                
            except Exception as e:
                self.logger.error(f"Error in batch calculation for character {character.character_id}: {e}")
                continue
        
        # Sort by final score descending
        scores.sort(key=lambda x: x.final_score, reverse=True)
        
        self.logger.info(f"Calculated trending scores for {len(scores)} characters")
        return scores
    
    def _calculate_base_character_score(self, character: CharacterData) -> float:
        """Calculate base score from character metrics"""
        # Logarithmic scaling to prevent extreme values
        favourites_score = math.log10(max(1, character.favourites)) * 10
        
        # Media appearance factor
        media_factor = min(5.0, len(character.media_appearances) * 0.5)
        
        # Role quality factor
        main_roles = sum(1 for m in character.media_appearances if m.get('role') == 'MAIN')
        role_quality = min(3.0, main_roles * 0.8)
        
        base_score = favourites_score + media_factor + role_quality
        return max(1.0, base_score)
    
    def _calculate_base_media_score(self, media: TrendingData) -> float:
        """Calculate base score from media metrics"""
        # Logarithmic scaling for large numbers
        popularity_score = math.log10(max(1, media.popularity)) * 8
        favourites_score = math.log10(max(1, media.favourites)) * 6
        
        # Trending rank (inverse - lower rank is better)
        trending_score = max(0, 10 - (media.trending_rank / 10)) if media.trending_rank else 0
        
        base_score = popularity_score + favourites_score + trending_score
        return max(1.0, base_score)
    
    def _calculate_gender_boost(self, gender: Optional[str]) -> float:
        """Apply gender boost based on preferences"""
        return self.gender_boosts.get(gender, 1.0)
    
    def _calculate_character_recency_boost(
        self,
        character: CharacterData,
        related_media: List[TrendingData] = None
    ) -> float:
        """Calculate recency boost based on recent media appearances"""
        if not character.media_appearances and not related_media:
            return 1.0
        
        current_year = datetime.now().year
        recent_media_count = 0
        
        # Check character's media appearances
        for media_appearance in character.media_appearances:
            # Try to extract year from media data
            if 'season_year' in media_appearance:
                year = media_appearance.get('season_year')
                if year and current_year - year <= 2:
                    recent_media_count += 1
        
        # Check related media from context
        if related_media:
            for media in related_media:
                if media.season_year and current_year - media.season_year <= 2:
                    recent_media_count += 1
        
        # Apply recency boost
        if recent_media_count >= 3:
            return 1.5
        elif recent_media_count >= 2:
            return 1.3
        elif recent_media_count >= 1:
            return 1.1
        else:
            return 1.0
    
    def _calculate_media_recency_boost(self, media: TrendingData) -> float:
        """Calculate recency boost for media"""
        if not media.season_year:
            return 1.0
        
        current_year = datetime.now().year
        years_old = current_year - media.season_year
        
        if years_old <= 0:  # Current year
            return 1.5
        elif years_old <= 1:  # Last year
            return 1.3
        elif years_old <= 2:  # 2 years ago
            return 1.1
        elif years_old <= 5:  # 3-5 years ago
            return 1.0
        else:  # Older
            return 0.9
    
    def _calculate_character_quality_boost(
        self,
        character: CharacterData,
        related_media: List[TrendingData] = None
    ) -> float:
        """Calculate quality boost based on media scores"""
        scores = []
        
        # Get scores from character's media appearances
        for media_appearance in character.media_appearances:
            if 'average_score' in media_appearance and media_appearance['average_score']:
                scores.append(media_appearance['average_score'])
        
        # Get scores from related media context
        if related_media:
            for media in related_media:
                if media.average_score:
                    scores.append(media.average_score)
        
        if not scores:
            return 1.0
        
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 85:
            return 1.4
        elif avg_score >= 80:
            return 1.2
        elif avg_score >= 75:
            return 1.1
        elif avg_score >= 70:
            return 1.0
        else:
            return 0.9
    
    def _calculate_media_quality_boost(self, media: TrendingData) -> float:
        """Calculate quality boost for media"""
        if not media.average_score:
            return 1.0
        
        score = media.average_score
        
        if score >= 90:
            return 1.5
        elif score >= 85:
            return 1.3
        elif score >= 80:
            return 1.2
        elif score >= 75:
            return 1.1
        elif score >= 70:
            return 1.0
        else:
            return 0.9
    
    def _calculate_role_boost(self, character: CharacterData) -> float:
        """Calculate boost based on character roles"""
        if not character.media_appearances:
            return 1.0
        
        role_scores = []
        for media_appearance in character.media_appearances:
            role = media_appearance.get('role')
            weight = self.role_weights.get(role, 0.5)
            role_scores.append(weight)
        
        # Average role weight with boost for multiple significant roles
        avg_role_weight = sum(role_scores) / len(role_scores)
        main_roles = sum(1 for score in role_scores if score >= 1.0)
        
        # Boost for multiple main roles
        main_role_boost = 1.0 + (main_roles - 1) * 0.1 if main_roles > 1 else 1.0
        
        return avg_role_weight * main_role_boost
    
    def _calculate_character_diversity_boost(self, media: TrendingData) -> float:
        """Calculate boost based on character diversity in media"""
        if not media.characters:
            return 1.0
        
        character_count = len(media.characters)
        main_characters = sum(1 for c in media.characters if c.get('role') == 'MAIN')
        
        # Boost for good character variety
        if character_count >= 8 and main_characters >= 2:
            return 1.2
        elif character_count >= 5 and main_characters >= 1:
            return 1.1
        else:
            return 1.0
    
    def _calculate_historical_momentum(self, historical_data: List[HistoricalData]) -> float:
        """Calculate momentum boost from historical trending data"""
        if not historical_data or len(historical_data) < 2:
            return 1.0
        
        # Sort by timestamp
        sorted_data = sorted(historical_data, key=lambda x: x.timestamp)
        recent_data = sorted_data[-3:]  # Last 3 data points
        
        if len(recent_data) < 2:
            return 1.0
        
        # Calculate trend
        scores = [data.trending_score for data in recent_data]
        
        # Simple momentum calculation
        recent_avg = sum(scores[-2:]) / 2
        older_avg = sum(scores[:-2]) / max(1, len(scores) - 2) if len(scores) > 2 else scores[0]
        
        if recent_avg > older_avg * 1.2:
            return 1.3  # Strong upward trend
        elif recent_avg > older_avg * 1.1:
            return 1.15  # Moderate upward trend
        elif recent_avg < older_avg * 0.8:
            return 0.9   # Downward trend
        else:
            return 1.0   # Stable
    
    def _get_average_media_score(self, media_appearances: List[Dict[str, Any]]) -> float:
        """Get average score from media appearances"""
        scores = [
            media.get('average_score', 0) 
            for media in media_appearances 
            if media.get('average_score')
        ]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _count_recent_media(self, media_appearances: List[Dict[str, Any]]) -> int:
        """Count recent media appearances (last 2 years)"""
        current_year = datetime.now().year
        count = 0
        
        for media in media_appearances:
            season_year = media.get('season_year')
            if season_year and current_year - season_year <= 2:
                count += 1
        
        return count

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class TemperatureLevel(str, Enum):
    HOT = "HOT"
    WARM = "WARM"
    MILD = "MILD"
    COLD = "COLD"
    FROZEN = "FROZEN"

@dataclass
class CharacterData:
    character_id: str
    favourites: int
    trend_direction: str = "STABLE"
    velocity: float = 0.0
    acceleration: float = 0.0
    growth_percentage: float = 0.0
    media_title: Optional[str] = None
    anilist_id: Optional[int] = None
    last_updated: Optional[datetime] = None

@dataclass
class TemperatureResult:
    temperature: str
    reason: str
    next_update_due: datetime
    confidence: float = 1.0

class TemperatureEngine:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    def classify_character(self, character_data: CharacterData) -> TemperatureResult:
        favourites = character_data.favourites
        trend = character_data.trend_direction
        velocity = character_data.velocity
        acceleration = character_data.acceleration
        growth = character_data.growth_percentage

        # Regole per temperature con trend data
        if trend in ["VIRAL", "BREAKOUT"] and growth >= 50.0:
            return TemperatureResult(
                temperature="HOT",
                reason="hot_viral_characters",
                next_update_due=datetime.now() + timedelta(hours=3)
            )
        
        if favourites >= 10000 and velocity >= 100 and acceleration >= 20:
            return TemperatureResult(
                temperature="HOT", 
                reason="hot_accelerating_popular",
                next_update_due=datetime.now() + timedelta(hours=6)
            )
        
        if favourites >= 15000:
            return TemperatureResult(
                temperature="HOT",
                reason="hot_trending_characters", 
                next_update_due=datetime.now() + timedelta(hours=6)
            )
        
        if trend in ["RISING", "ACCELERATING"] and velocity >= 25 and favourites >= 2000:
            return TemperatureResult(
                temperature="WARM",
                reason="warm_rising_momentum",
                next_update_due=datetime.now() + timedelta(hours=12)
            )
        
        if 5000 <= favourites < 15000:
            return TemperatureResult(
                temperature="WARM",
                reason="warm_popular_characters",
                next_update_due=datetime.now() + timedelta(hours=24)
            )
        
        if trend in ["RISING", "STABLE"] and 5 <= velocity < 25 and favourites >= 500:
            return TemperatureResult(
                temperature="MILD",
                reason="mild_stable_growth", 
                next_update_due=datetime.now() + timedelta(days=2)
            )
        
        if 1000 <= favourites < 5000:
            return TemperatureResult(
                temperature="MILD",
                reason="mild_medium_characters",
                next_update_due=datetime.now() + timedelta(days=3)
            )
        
        if trend in ["FALLING", "DECELERATING"] and velocity < -10:
            return TemperatureResult(
                temperature="COLD",
                reason="cold_declining_characters",
                next_update_due=datetime.now() + timedelta(days=7)
            )
        
        if 200 <= favourites < 1000:
            return TemperatureResult(
                temperature="COLD",
                reason="cold_regular_characters",
                next_update_due=datetime.now() + timedelta(days=7)
            )
        
        if trend == "VOLATILE" and velocity < -20 and favourites < 500:
            return TemperatureResult(
                temperature="FROZEN",
                reason="frozen_volatile_declining",
                next_update_due=datetime.now() + timedelta(days=30)
            )
        
        # Default
        return TemperatureResult(
            temperature="FROZEN",
            reason="frozen_unpopular_characters",
            next_update_due=datetime.now() + timedelta(days=30)
        )

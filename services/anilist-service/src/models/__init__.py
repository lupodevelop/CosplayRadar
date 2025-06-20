"""
Modelli dati per il servizio AniList
Definisce le strutture dati per personaggi, serie e dati storici
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl


class Gender(str, Enum):
    """Generi supportati da AniList"""
    MALE = "MALE"
    FEMALE = "FEMALE"
    NON_BINARY = "NON_BINARY"


class MediaStatus(str, Enum):
    """Stati delle serie su AniList"""
    RELEASING = "RELEASING"
    FINISHED = "FINISHED"
    NOT_YET_RELEASED = "NOT_YET_RELEASED"
    CANCELLED = "CANCELLED"
    HIATUS = "HIATUS"


class CharacterRole(str, Enum):
    """Ruoli dei personaggi nelle serie"""
    MAIN = "MAIN"
    SUPPORTING = "SUPPORTING"
    BACKGROUND = "BACKGROUND"


class MediaFormat(str, Enum):
    """Formati delle serie"""
    TV = "TV"
    TV_SHORT = "TV_SHORT"
    MOVIE = "MOVIE"
    SPECIAL = "SPECIAL"
    OVA = "OVA"
    ONA = "ONA"
    MUSIC = "MUSIC"


class MediaType(str, Enum):
    """Tipi di media su AniList"""
    ANIME = "ANIME"
    MANGA = "MANGA"


class CharacterName(BaseModel):
    """Nomi del personaggio in diverse lingue"""
    first: Optional[str] = None
    middle: Optional[str] = None
    last: Optional[str] = None
    full: Optional[str] = None
    native: Optional[str] = None
    alternative: List[str] = Field(default_factory=list)
    alternative_spoiler: List[str] = Field(default_factory=list)


class CharacterImage(BaseModel):
    """Immagini del personaggio"""
    large: Optional[HttpUrl] = None
    medium: Optional[HttpUrl] = None


class MediaTitle(BaseModel):
    """Titoli della serie in diverse lingue"""
    romaji: Optional[str] = None
    english: Optional[str] = None
    native: Optional[str] = None


class MediaDate(BaseModel):
    """Date AniList (anno, mese, giorno)"""
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None

    def to_date(self) -> Optional[date]:
        """Converte in oggetto date Python"""
        if self.year:
            return date(
                self.year,
                self.month or 1,
                self.day or 1
            )
        return None


class CharacterMedia(BaseModel):
    """Serie associate al personaggio"""
    id: int
    title: MediaTitle
    trending: int = 0
    popularity: int = 0
    average_score: Optional[int] = None
    status: MediaStatus
    start_date: Optional[MediaDate] = None
    format: Optional[MediaFormat] = None
    character_role: CharacterRole
    
    # Metadati
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Character(BaseModel):
    """Personaggio AniList completo"""
    id: int
    name: CharacterName
    image: Optional[CharacterImage] = None
    description: Optional[str] = None
    gender: Optional[Gender] = None
    age: Optional[str] = None
    blood_type: Optional[str] = None
    date_of_birth: Optional[MediaDate] = None
    site_url: Optional[HttpUrl] = None
    favourites: int = 0
    is_favourite: bool = False
    
    # Serie associate
    media: List[CharacterMedia] = Field(default_factory=list)
    
    # Metadati
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TrendingScoreData(BaseModel):
    """Dati del trending score calcolato"""
    character_id: int
    trending_score: float
    base_score: float
    
    # Boost applicati
    gender_boost: float = 1.0
    recency_boost: float = 1.0
    quality_boost: float = 1.0
    total_boost_multiplier: float = 1.0
    
    # Dati contribuenti
    character_favourites: int
    avg_series_trending: float
    max_series_trending: int
    total_series: int
    main_roles_count: int
    
    # Metadati
    calculated_at: datetime = Field(default_factory=datetime.now)
    algorithm_version: str = "1.0"


class PeriodType(str, Enum):
    """Tipi di periodo per aggregazione dati storici"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class HistoricalDataPoint(BaseModel):
    """Punto dati storico aggregato"""
    character_id: int
    period_type: PeriodType
    period_date: date
    
    # Dati aggregati
    favourites_avg: float
    favourites_min: int
    favourites_max: int
    trending_score_avg: float
    trending_score_peak: float
    data_points: int  # Numero di campioni aggregati
    
    # Metadati
    created_at: datetime = Field(default_factory=datetime.now)


class SyncResult(BaseModel):
    """Risultato di una sincronizzazione"""
    success: bool
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Statistiche
    characters_processed: int = 0
    characters_updated: int = 0
    characters_created: int = 0
    series_processed: int = 0
    errors: List[str] = Field(default_factory=list)
    
    # Rate limiting info
    requests_made: int = 0
    rate_limit_hits: int = 0
    
    def duration(self) -> Optional[float]:
        """Durata dell'operazione in secondi"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class AniListConfig(BaseModel):
    """Configurazione per il servizio AniList"""
    # API Settings
    api_url: str = "https://graphql.anilist.co"
    rate_limit_per_minute: int = 90
    request_timeout: int = 30
    
    # Database
    database_url: str
    
    # Trending Algorithm
    gender_boost_female: float = 1.3
    recency_boost_months: int = 6
    recency_boost_multiplier: float = 1.5
    quality_score_threshold: int = 85
    quality_boost_multiplier: float = 1.1
    
    # Data Retention
    daily_retention_days: int = 30
    weekly_retention_weeks: int = 52
    monthly_retention_months: int = 24
    yearly_retention_years: int = 5
    
    # Processing
    batch_size: int = 25
    max_concurrent_requests: int = 5
    
    # Scheduling
    sync_schedule: str = "0 6 * * *"  # Daily at 6 AM UTC
    cleanup_schedule: str = "0 2 * * 0"  # Weekly at 2 AM UTC Sunday


class DatabaseConfig(BaseModel):
    """Configurazione database"""
    type: Literal["sqlite", "postgresql"] = "postgresql"
    url: str = "postgresql://postgres:postgres@localhost:5432/cosplayradar_dev"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30


class ServiceConfig(BaseModel):
    """Configurazione completa del servizio"""
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    anilist: AniListConfig = Field(default_factory=AniListConfig)
    
    # Sync configuration
    character_batch_size: int = 100
    media_batch_size: int = 50
    full_sync_character_limit: int = 1000
    daily_sync_character_limit: int = 200
    
    # Data freshness thresholds (hours)
    character_data_max_age: int = 168  # 7 days
    media_data_max_age: int = 24       # 1 day
    trending_data_max_age: int = 1     # 1 hour
    
    # Update strategy
    skip_update_threshold: float = 0.05  # 5% change threshold
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "structured"


class MediaData(BaseModel):
    """Dati completi di una serie (anime/manga)"""
    id: int
    title: MediaTitle
    type: MediaType
    format: Optional[MediaFormat] = None
    status: MediaStatus
    description: Optional[str] = None
    start_date: Optional[MediaDate] = None
    end_date: Optional[MediaDate] = None
    season: Optional[str] = None
    season_year: Optional[int] = None
    episodes: Optional[int] = None
    duration: Optional[int] = None
    chapters: Optional[int] = None
    volumes: Optional[int] = None
    country_of_origin: Optional[str] = None
    is_licensed: bool = False
    source: Optional[str] = None
    hashtag: Optional[str] = None
    trailer: Optional[Dict[str, Any]] = None
    updated_at: Optional[int] = None
    cover_image: Optional[Dict[str, Any]] = None
    banner_image: Optional[HttpUrl] = None
    genres: List[str] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)
    average_score: Optional[int] = None
    mean_score: Optional[int] = None
    popularity: int = 0
    trending: int = 0
    favourites: int = 0
    tags: List[Dict[str, Any]] = Field(default_factory=list)
    is_adult: bool = False
    next_airing_episode: Optional[Dict[str, Any]] = None
    site_url: Optional[HttpUrl] = None
    
    # Metadati
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Export all models
__all__ = [
    # Enums
    "Gender", "CharacterRole", "MediaStatus", "MediaFormat", "MediaType", "PeriodType",
    
    # Models
    "CharacterName", "CharacterImage", "MediaTitle", "MediaDate",
    "CharacterMedia", "Character", "TrendingScoreData", "HistoricalDataPoint",
    "SyncResult", "MediaData",
    
    # Configuration
    "AniListConfig", "DatabaseConfig", "ServiceConfig"
]

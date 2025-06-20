"""
SQLAlchemy database models for AniList service
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, 
    JSON, ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class MediaTypeEnum(enum.Enum):
    ANIME = "ANIME"
    MANGA = "MANGA"


class AggregationPeriodEnum(enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class Character(Base):
    """Character database model"""
    __tablename__ = 'characters'
    
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    name_native = Column(String(255))
    alternative_names = Column(JSON)
    description = Column(Text)
    gender = Column(String(50), index=True)
    age = Column(Integer)
    favourites = Column(Integer, default=0, index=True)
    image_large = Column(String(500))
    image_medium = Column(String(500))
    popularity_tier = Column(String(10), index=True)
    cosplay_potential = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_fetched = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    media_appearances = relationship("CharacterMedia", back_populates="character", cascade="all, delete-orphan")
    trending_scores = relationship("TrendingScore", back_populates="character", cascade="all, delete-orphan")
    historical_data = relationship("HistoricalData", back_populates="character", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_character_favourites_desc', favourites.desc()),
        Index('idx_character_gender_favourites', gender, favourites.desc()),
        Index('idx_character_updated_at', updated_at.desc()),
    )


class Media(Base):
    """Media (anime/manga) database model"""
    __tablename__ = 'media'
    
    id = Column(Integer, primary_key=True)
    media_id = Column(Integer, unique=True, nullable=False, index=True)
    title_romaji = Column(String(500), index=True)
    title_english = Column(String(500), index=True)
    title_native = Column(String(500))
    media_type = Column(SQLEnum(MediaTypeEnum), nullable=False, index=True)
    format = Column(String(50))
    status = Column(String(50), index=True)
    description = Column(Text)
    
    # Dates
    start_year = Column(Integer, index=True)
    start_month = Column(Integer)
    start_day = Column(Integer)
    end_year = Column(Integer)
    end_month = Column(Integer)
    end_day = Column(Integer)
    season = Column(String(20), index=True)
    season_year = Column(Integer, index=True)
    
    # Numbers
    episodes = Column(Integer)
    duration = Column(Integer)
    chapters = Column(Integer)
    volumes = Column(Integer)
    
    # Popularity metrics
    popularity = Column(Integer, default=0, index=True)
    favourites = Column(Integer, default=0, index=True)
    average_score = Column(Integer, index=True)
    mean_score = Column(Integer)
    trending_rank = Column(Integer, index=True)
    
    # Media content
    genres = Column(JSON)
    tags = Column(JSON)
    cover_image_large = Column(String(500))
    cover_image_medium = Column(String(500))
    banner_image = Column(String(500))
    
    # Calculated fields
    popularity_tier = Column(String(10), index=True)
    quality_tier = Column(String(10), index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_fetched = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    character_appearances = relationship("CharacterMedia", back_populates="media", cascade="all, delete-orphan")
    studios = relationship("MediaStudio", back_populates="media", cascade="all, delete-orphan")
    trending_scores = relationship("TrendingScore", back_populates="media", cascade="all, delete-orphan")
    historical_data = relationship("HistoricalData", back_populates="media", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_media_popularity_desc', popularity.desc()),
        Index('idx_media_score_desc', average_score.desc()),
        Index('idx_media_trending_desc', trending_rank.desc()),
        Index('idx_media_season_year', season, season_year.desc()),
        Index('idx_media_type_status', media_type, status),
        Index('idx_media_updated_at', updated_at.desc()),
    )


class CharacterMedia(Base):
    """Character-Media relationship model"""
    __tablename__ = 'character_media'
    
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=False)
    media_id = Column(Integer, ForeignKey('media.id'), nullable=False)
    
    # Role information
    role = Column(String(50), index=True)  # MAIN, SUPPORTING, BACKGROUND
    voice_actors = Column(JSON)
    
    # Media-specific character data
    media_popularity = Column(Integer, default=0)
    media_favourites = Column(Integer, default=0)
    media_average_score = Column(Integer)
    media_trending = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    character = relationship("Character", back_populates="media_appearances")
    media = relationship("Media", back_populates="character_appearances")
    
    # Indexes
    __table_args__ = (
        Index('idx_character_media_unique', character_id, media_id, unique=True),
        Index('idx_character_media_role', character_id, role),
        Index('idx_media_character_role', media_id, role),
    )


class Studio(Base):
    """Studio database model"""
    __tablename__ = 'studios'
    
    id = Column(Integer, primary_key=True)
    studio_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    is_animation_studio = Column(Boolean, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    media = relationship("MediaStudio", back_populates="studio")


class MediaStudio(Base):
    """Media-Studio relationship model"""
    __tablename__ = 'media_studios'
    
    id = Column(Integer, primary_key=True)
    media_id = Column(Integer, ForeignKey('media.id'), nullable=False)
    studio_id = Column(Integer, ForeignKey('studios.id'), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    media = relationship("Media", back_populates="studios")
    studio = relationship("Studio", back_populates="media")
    
    # Indexes
    __table_args__ = (
        Index('idx_media_studio_unique', media_id, studio_id, unique=True),
    )


class TrendingScore(Base):
    """Trending score database model"""
    __tablename__ = 'trending_scores'
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, nullable=False, index=True)
    entity_type = Column(String(20), nullable=False, index=True)  # 'character' or 'media'
    
    # Score components
    base_score = Column(Float, nullable=False)
    gender_boost = Column(Float, default=1.0)
    recency_boost = Column(Float, default=1.0)
    quality_boost = Column(Float, default=1.0)
    role_boost = Column(Float, default=1.0)
    momentum_boost = Column(Float, default=1.0)
    final_score = Column(Float, nullable=False, index=True)
    
    # Metadata
    calculation_details = Column(JSON)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign keys (nullable because entity can be character or media)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=True)
    media_id = Column(Integer, ForeignKey('media.id'), nullable=True)
    
    # Relationships
    character = relationship("Character", back_populates="trending_scores")
    media = relationship("Media", back_populates="trending_scores")
    
    # Indexes
    __table_args__ = (
        Index('idx_trending_score_entity', entity_type, entity_id),
        Index('idx_trending_score_final_desc', final_score.desc()),
        Index('idx_trending_score_timestamp_desc', timestamp.desc()),
        Index('idx_trending_score_entity_timestamp', entity_type, entity_id, timestamp.desc()),
    )


class HistoricalData(Base):
    """Historical trending data model"""
    __tablename__ = 'historical_data'
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, nullable=False, index=True)
    entity_type = Column(String(20), nullable=False, index=True)  # 'character' or 'media'
    
    # Historical metrics
    trending_score = Column(Float, nullable=False)
    popularity_rank = Column(Integer, index=True)
    
    # Aggregation info
    aggregation_period = Column(SQLEnum(AggregationPeriodEnum), nullable=False, index=True)
    data_points = Column(Integer, default=1)  # Number of original data points aggregated
    
    # Additional metadata
    additional_metadata = Column(JSON)
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign keys (nullable because entity can be character or media)
    character_id = Column(Integer, ForeignKey('characters.id'), nullable=True)
    media_id = Column(Integer, ForeignKey('media.id'), nullable=True)
    
    # Relationships
    character = relationship("Character", back_populates="historical_data")
    media = relationship("Media", back_populates="historical_data")
    
    # Indexes
    __table_args__ = (
        Index('idx_historical_entity', entity_type, entity_id),
        Index('idx_historical_timestamp_desc', timestamp.desc()),
        Index('idx_historical_period', aggregation_period, timestamp.desc()),
        Index('idx_historical_entity_period', entity_type, entity_id, aggregation_period, timestamp.desc()),
        Index('idx_historical_score_desc', trending_score.desc()),
    )


class DataFetchLog(Base):
    """Log of data fetch operations"""
    __tablename__ = 'data_fetch_logs'
    
    id = Column(Integer, primary_key=True)
    operation_type = Column(String(50), nullable=False, index=True)  # 'trending', 'characters', 'media'
    status = Column(String(20), nullable=False, index=True)  # 'success', 'error', 'partial'
    
    # Metrics
    records_fetched = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    records_saved = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    # Details
    details = Column(JSON)
    error_message = Column(Text)
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('idx_fetch_log_operation', operation_type, started_at.desc()),
        Index('idx_fetch_log_status', status, started_at.desc()),
    )


class SystemConfig(Base):
    """System configuration model"""
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text)
    value_type = Column(String(20), default='string')  # 'string', 'int', 'float', 'bool', 'json'
    description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

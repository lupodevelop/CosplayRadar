"""
Schema SQLAlchemy per AniList Service
Schema autonomo e estensibile per dati AniList e futuri servizi
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, 
    create_engine, event, text
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


# ==========================================
# TABELLE CORE - DATI ANILIST
# ==========================================

class AniListCharacter(Base):
    """
    Personaggi da AniList - Tabella principale
    Contiene tutti i dati dei personaggi recuperati da AniList API
    """
    __tablename__ = 'anilist_characters'
    
    # Primary Key
    id = Column(Integer, primary_key=True)  # AniList ID diretto
    
    # Nome completo (multilingua)
    name_full = Column(String(255), nullable=True, index=True)
    name_first = Column(String(128), nullable=True)
    name_middle = Column(String(128), nullable=True)
    name_last = Column(String(128), nullable=True)
    name_native = Column(String(255), nullable=True, index=True)
    name_alternative = Column(ARRAY(String), nullable=True)
    name_alternative_spoiler = Column(ARRAY(String), nullable=True)
    
    # Immagini
    image_large = Column(String(500), nullable=True)
    image_medium = Column(String(500), nullable=True)
    
    # Informazioni personaggio
    description = Column(Text, nullable=True)
    gender = Column(String(20), nullable=True, index=True)
    age = Column(String(50), nullable=True)  # Può essere "16-17" o "Unknown"
    blood_type = Column(String(10), nullable=True)
    
    # Data di nascita (fuzzy date)
    birth_year = Column(Integer, nullable=True)
    birth_month = Column(Integer, nullable=True)
    birth_day = Column(Integer, nullable=True)
    
    # Metriche AniList
    favourites = Column(Integer, default=0, index=True)
    is_favourite = Column(Boolean, default=False)
    is_favourite_blocked = Column(Boolean, default=False)
    
    # URLs e metadati
    site_url = Column(String(500), nullable=True)
    mod_notes = Column(Text, nullable=True)
    
    # Tracking del servizio
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_fetched_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relazioni
    media_appearances = relationship("AniListCharacterMedia", back_populates="character")
    trending_snapshots = relationship("AniListTrendingSnapshot", back_populates="character")
    aggregated_data = relationship("AniListAggregatedData", back_populates="character")
    favourites_history = relationship("CharacterFavouritesHistory", back_populates="character")
    
    # Indici per performance
    __table_args__ = (
        Index('idx_character_name_full', name_full),
        Index('idx_character_favourites_desc', favourites.desc()),
        Index('idx_character_gender_favourites', gender, favourites.desc()),
        Index('idx_character_updated_at', updated_at),
        Index('idx_character_last_fetched', last_fetched_at),
    )


class AniListMedia(Base):
    """
    Anime/Manga da AniList - Serie e opere
    """
    __tablename__ = 'anilist_media'
    
    # Primary Key
    id = Column(Integer, primary_key=True)  # AniList ID diretto
    mal_id = Column(Integer, nullable=True, index=True)  # MyAnimeList ID
    
    # Titoli (multilingua)
    title_romaji = Column(String(255), nullable=True, index=True)
    title_english = Column(String(255), nullable=True, index=True)
    title_native = Column(String(255), nullable=True)
    title_user_preferred = Column(String(255), nullable=True)
    
    # Tipo e formato
    type = Column(String(20), nullable=False, index=True)  # ANIME, MANGA
    format = Column(String(30), nullable=True, index=True)  # TV, MOVIE, OVA, etc.
    status = Column(String(30), nullable=True, index=True)  # FINISHED, RELEASING, etc.
    
    # Descrizione e metadati
    description = Column(Text, nullable=True)
    start_date_year = Column(Integer, nullable=True)
    start_date_month = Column(Integer, nullable=True)
    start_date_day = Column(Integer, nullable=True)
    end_date_year = Column(Integer, nullable=True)
    end_date_month = Column(Integer, nullable=True) 
    end_date_day = Column(Integer, nullable=True)
    
    # Stagione e anno
    season = Column(String(20), nullable=True, index=True)  # SPRING, SUMMER, etc.
    season_year = Column(Integer, nullable=True, index=True)
    season_int = Column(Integer, nullable=True)
    
    # Episodi e durata
    episodes = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)  # minuti per episodio
    chapters = Column(Integer, nullable=True)  # per manga
    volumes = Column(Integer, nullable=True)   # per manga
    
    # Origine e source
    country_of_origin = Column(String(5), nullable=True)  # JP, KR, CN, etc.
    source = Column(String(30), nullable=True)  # MANGA, LIGHT_NOVEL, etc.
    hashtag = Column(String(100), nullable=True)
    
    # Immagini
    cover_image_extra_large = Column(String(500), nullable=True)
    cover_image_large = Column(String(500), nullable=True)
    cover_image_medium = Column(String(500), nullable=True)
    cover_image_color = Column(String(10), nullable=True)
    banner_image = Column(String(500), nullable=True)
    
    # Generi e tag
    genres = Column(ARRAY(String), nullable=True)
    synonyms = Column(ARRAY(String), nullable=True)
    tags = Column(JSONB, nullable=True)  # Array di oggetti tag complessi
    
    # Score e popolarità
    average_score = Column(Integer, nullable=True, index=True)
    mean_score = Column(Integer, nullable=True)
    popularity = Column(Integer, default=0, index=True)
    favourites = Column(Integer, default=0, index=True)
    trending = Column(Integer, default=0, index=True)
    
    # Status e flags
    is_locked = Column(Boolean, default=False)
    is_adult = Column(Boolean, default=False)
    is_favourite = Column(Boolean, default=False)
    is_favourite_blocked = Column(Boolean, default=False)
    is_licensed = Column(Boolean, default=False)
    
    # URLs e links esterni
    site_url = Column(String(500), nullable=True)
    external_links = Column(JSONB, nullable=True)
    streaming_episodes = Column(JSONB, nullable=True)
    
    # Relazioni e rankings
    relations = Column(JSONB, nullable=True)
    rankings = Column(JSONB, nullable=True)
    
    # Studios
    studios = Column(JSONB, nullable=True)  # Array di studios
    
    # Tracking del servizio
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_fetched_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relazioni
    character_appearances = relationship("AniListCharacterMedia", back_populates="media")
    trending_snapshots = relationship("AniListTrendingSnapshot", back_populates="media")
    
    # Indici per performance
    __table_args__ = (
        Index('idx_media_type_status', type, status),
        Index('idx_media_season_year', season, season_year),
        Index('idx_media_popularity_desc', popularity.desc()),
        Index('idx_media_trending_desc', trending.desc()),
        Index('idx_media_average_score_desc', average_score.desc()),
        Index('idx_media_start_date', start_date_year, start_date_month),
        Index('idx_media_updated_at', updated_at),
    )


class AniListCharacterMedia(Base):
    """
    Relazioni Personaggio-Media con ruoli
    """
    __tablename__ = 'anilist_character_media'
    
    # Composite Primary Key
    character_id = Column(Integer, ForeignKey('anilist_characters.id'), primary_key=True)
    media_id = Column(Integer, ForeignKey('anilist_media.id'), primary_key=True)
    
    # Ruolo del personaggio
    role = Column(String(20), nullable=False, index=True)  # MAIN, SUPPORTING, BACKGROUND
    
    # Voice actors (JSONB per flessibilità)
    voice_actors = Column(JSONB, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relazioni
    character = relationship("AniListCharacter", back_populates="media_appearances")
    media = relationship("AniListMedia", back_populates="character_appearances")
    
    # Indici
    __table_args__ = (
        Index('idx_char_media_role', role),
        Index('idx_char_media_character', character_id),
        Index('idx_char_media_media', media_id),
    )


# ==========================================
# TABELLE TRENDING E ANALYTICS
# ==========================================

class AniListTrendingSnapshot(Base):
    """
    Snapshot giornalieri dei trending scores
    """
    __tablename__ = 'anilist_trending_snapshots'
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    character_id = Column(Integer, ForeignKey('anilist_characters.id'), nullable=True, index=True)
    media_id = Column(Integer, ForeignKey('anilist_media.id'), nullable=True, index=True)
    
    # Tipo di entità
    entity_type = Column(String(20), nullable=False, index=True)  # 'character', 'media'
    
    # Data e periodo
    snapshot_date = Column(Date, nullable=False, index=True)
    period_type = Column(String(20), nullable=False, index=True)  # 'daily', 'weekly'
    
    # Ranking ufficiale AniList
    anilist_rank = Column(Integer, nullable=True, index=True)
    anilist_trending_score = Column(Integer, default=0)  # Score trending AniList
    
    # Nostro trending score calcolato
    calculated_trending_score = Column(Float, nullable=False, index=True)
    
    # Componenti dettagliati del calcolo (per debugging e analisi)
    base_score = Column(Float, nullable=True)
    growth_multiplier = Column(Float, nullable=True)
    series_boost = Column(Float, nullable=True)
    gender_boost = Column(Float, nullable=True)
    role_boost = Column(Float, nullable=True)
    recency_factor = Column(Float, nullable=True)
    
    # Metadati calcolo
    calculation_metadata = Column(JSONB, nullable=True)  # Dettagli extra per debugging
    
    # Componenti del score
    base_score_old = Column(Float, nullable=False)  # Mantengo per backward compatibility
    gender_boost = Column(Float, default=1.0)
    recency_boost = Column(Float, default=1.0) 
    quality_boost = Column(Float, default=1.0)
    role_weight = Column(Float, default=1.0)
    total_boost_multiplier = Column(Float, default=1.0)
    
    # Metadati del calcolo
    algorithm_version = Column(String(10), default="1.0")
    calculation_metadata = Column(JSONB, nullable=True)
    
    # Dati denormalizzati per performance (character)
    character_name = Column(String(255), nullable=True)
    character_gender = Column(String(20), nullable=True)
    character_favourites = Column(Integer, nullable=True)
    character_image = Column(String(500), nullable=True)
    
    # Dati denormalizzati per performance (media)
    media_title = Column(String(255), nullable=True)
    media_type = Column(String(20), nullable=True)
    media_format = Column(String(30), nullable=True)
    media_popularity = Column(Integer, nullable=True)
    media_average_score = Column(Integer, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relazioni
    character = relationship("AniListCharacter", back_populates="trending_snapshots")
    media = relationship("AniListMedia", back_populates="trending_snapshots")
    
    # Indici per performance
    __table_args__ = (
        Index('idx_trending_date_type', snapshot_date, entity_type),
        Index('idx_trending_score_desc', calculated_trending_score.desc()),
        Index('idx_trending_character_date', character_id, snapshot_date),
        Index('idx_trending_media_date', media_id, snapshot_date),
        Index('idx_trending_rank', anilist_rank),
        UniqueConstraint('character_id', 'media_id', 'snapshot_date', 'period_type', 
                        name='uq_trending_entity_date_period'),
        CheckConstraint('(character_id IS NOT NULL) OR (media_id IS NOT NULL)', 
                       name='check_trending_entity_not_null'),
    )


class AniListAggregatedData(Base):
    """
    Dati aggregati per periodi (weekly, monthly, yearly)
    """
    __tablename__ = 'anilist_aggregated_data'
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    character_id = Column(Integer, ForeignKey('anilist_characters.id'), nullable=True, index=True)
    media_id = Column(Integer, ForeignKey('anilist_media.id'), nullable=True, index=True)
    
    # Tipo di entità
    entity_type = Column(String(20), nullable=False, index=True)
    
    # Periodo di aggregazione
    period_type = Column(String(20), nullable=False, index=True)  # 'weekly', 'monthly', 'yearly'
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    
    # Metriche aggregate
    avg_trending_score = Column(Float, nullable=False)
    max_trending_score = Column(Float, nullable=False) 
    min_trending_score = Column(Float, nullable=False)
    best_rank = Column(Integer, nullable=True)  # Miglior ranking nel periodo
    worst_rank = Column(Integer, nullable=True)
    days_in_trending = Column(Integer, default=0)  # Giorni presenti in trending
    total_snapshots = Column(Integer, default=0)   # Numero di snapshot nel periodo
    
    # Crescita e trend
    growth_rate = Column(Float, nullable=True)      # % crescita vs periodo precedente
    volatility = Column(Float, nullable=True)       # Volatilità del trending score
    trend_direction = Column(String(20), nullable=True)  # 'rising', 'stable', 'declining'
    
    # Snapshot dati entità (per performance)
    entity_snapshot = Column(JSONB, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relazioni
    character = relationship("AniListCharacter", back_populates="aggregated_data")
    
    # Indici
    __table_args__ = (
        Index('idx_aggregated_period', period_type, period_start),
        Index('idx_aggregated_entity_period', entity_type, period_type),
        Index('idx_aggregated_avg_score_desc', avg_trending_score.desc()),
        Index('idx_aggregated_character_period', character_id, period_type, period_start),
        UniqueConstraint('character_id', 'media_id', 'period_type', 'period_start',
                        name='uq_aggregated_entity_period'),
        CheckConstraint('(character_id IS NOT NULL) OR (media_id IS NOT NULL)',
                       name='check_aggregated_entity_not_null'),
    )


# ==========================================
# TABELLE DI SISTEMA E LOGGING
# ==========================================

class AniListSyncLog(Base):
    """
    Log delle sincronizzazioni
    """
    __tablename__ = 'anilist_sync_logs'
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Info sync
    sync_type = Column(String(20), nullable=False, index=True)  # 'full', 'daily', 'weekly'
    status = Column(String(20), nullable=False, index=True)     # 'running', 'completed', 'failed'
    
    # Timing
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Statistiche
    characters_processed = Column(Integer, default=0)
    characters_created = Column(Integer, default=0)
    characters_updated = Column(Integer, default=0)
    characters_skipped = Column(Integer, default=0)
    
    media_processed = Column(Integer, default=0)
    media_created = Column(Integer, default=0)
    media_updated = Column(Integer, default=0)
    media_skipped = Column(Integer, default=0)
    
    # API Stats
    api_requests_made = Column(Integer, default=0)
    api_rate_limit_hits = Column(Integer, default=0)
    api_errors = Column(Integer, default=0)
    
    # Errori e warning
    errors = Column(JSONB, nullable=True)
    warnings = Column(JSONB, nullable=True)
    
    # Metadati della sync
    config_snapshot = Column(JSONB, nullable=True)
    environment = Column(String(20), nullable=True)  # 'development', 'production'
    
    # Indici
    __table_args__ = (
        Index('idx_sync_type_status', sync_type, status),
        Index('idx_sync_started_at', started_at),
    )


class AniListServiceConfig(Base):
    """
    Configurazioni del servizio (per audit e rollback)
    """
    __tablename__ = 'anilist_service_configs'
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Versione config
    version = Column(String(20), nullable=False, index=True)
    is_active = Column(Boolean, default=False, index=True)
    
    # Configurazione completa
    config_data = Column(JSONB, nullable=False)
    
    # Metadati
    description = Column(String(255), nullable=True)
    environment = Column(String(20), nullable=False, index=True)
    
    # Tracking
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)  # User/service che ha creato
    
    # Indici
    __table_args__ = (
        Index('idx_config_active', is_active),
        Index('idx_config_version', version),
    )


# ==========================================
# TABELLE ESTENSIBILI PER FUTURI SERVIZI
# ==========================================

class ServiceData(Base):
    """
    Tabella generica per dati di altri servizi
    Estensibile per permettere ad altri servizi di aggiungere i loro dati
    """
    __tablename__ = 'service_data'
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identificazione servizio
    service_name = Column(String(50), nullable=False, index=True)
    service_version = Column(String(20), nullable=True)
    
    # Entità di riferimento
    entity_type = Column(String(50), nullable=False, index=True)  # 'character', 'media', 'user', etc.
    entity_id = Column(String(100), nullable=False, index=True)   # ID dell'entità
    external_entity_id = Column(Integer, nullable=True, index=True)  # Link a nostre tabelle
    
    # Tipo di dato
    data_type = Column(String(50), nullable=False, index=True)   # 'trending', 'social', 'metrics', etc.
    data_subtype = Column(String(50), nullable=True, index=True) # 'twitter', 'reddit', 'google', etc.
    
    # Dati JSON flessibili
    data_payload = Column(JSONB, nullable=False)
    
    # Metadati
    confidence_score = Column(Float, nullable=True)  # Confidenza del dato (0-1)
    quality_score = Column(Float, nullable=True)     # Qualità del dato (0-1)
    source_url = Column(String(500), nullable=True)  # URL sorgente
    
    # Validità temporale
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indici per query efficienti
    __table_args__ = (
        Index('idx_service_entity', service_name, entity_type, entity_id),
        Index('idx_service_data_type', service_name, data_type, data_subtype),
        Index('idx_service_external_entity', external_entity_id),
        Index('idx_service_valid_period', valid_from, valid_until),
        Index('idx_service_created_at', created_at),
    )


class ServiceMetrics(Base):
    """
    Metriche aggregate per tutti i servizi
    """
    __tablename__ = 'service_metrics'
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identificazione
    service_name = Column(String(50), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # 'counter', 'gauge', 'histogram'
    
    # Valore metrica
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20), nullable=True)  # 'count', 'percentage', 'seconds', etc.
    
    # Dimensioni (per filtering/grouping)
    dimensions = Column(JSONB, nullable=True)  # {'environment': 'prod', 'region': 'us', etc.}
    
    # Timing
    timestamp = Column(DateTime, nullable=False, index=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Indici
    __table_args__ = (
        Index('idx_metrics_service_name_timestamp', service_name, metric_name, timestamp),
        Index('idx_metrics_timestamp', timestamp),
        Index('idx_metrics_type', metric_type),
    )


class CharacterFavouritesHistory(Base):
    """
    Storico dei favourites per calcolare la crescita nel tempo
    """
    __tablename__ = 'character_favourites_history'
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    character_id = Column(Integer, ForeignKey('anilist_characters.id'), nullable=False, index=True)
    
    # Dati favourites
    favourites = Column(Integer, nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metadati
    created_at = Column(DateTime(timezone=True), default=func.now())
    
    # Relationships
    character = relationship("AniListCharacter", back_populates="favourites_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_char_fav_hist_char_date', 'character_id', 'recorded_at'),
        Index('idx_char_fav_hist_recorded', 'recorded_at'),
    )


class TrendingConfig(Base):
    """
    Configurazione dei moltiplicatori per l'algoritmo di trending
    """
    __tablename__ = 'trending_config'
    
    # Primary Key
    key = Column(String(100), primary_key=True)
    
    # Valori configurazione
    value_float = Column(Float, nullable=True)
    value_string = Column(String(255), nullable=True)
    value_int = Column(Integer, nullable=True)
    value_bool = Column(Boolean, nullable=True)
    
    # Metadati
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)  # es: 'gender_boost', 'role_boost'
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), default=func.now())


# ==========================================
# FUNZIONI E TRIGGER (PostgreSQL)
# ==========================================

def create_updated_at_trigger():
    """
    SQL per creare trigger automatico di updated_at
    """
    return """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """

def apply_updated_at_triggers(engine):
    """
    Applica trigger updated_at a tutte le tabelle che hanno la colonna
    """
    trigger_sql = create_updated_at_trigger()
    
    tables_with_updated_at = [
        'anilist_characters',
        'anilist_media', 
        'anilist_character_media',
        'service_data'
    ]
    
    with engine.connect() as conn:
        # Crea la funzione
        conn.execute(text(trigger_sql))
        
        # Applica trigger a ogni tabella
        for table in tables_with_updated_at:
            trigger_name = f"trigger_update_{table}_updated_at"
            conn.execute(text(f"""
                DROP TRIGGER IF EXISTS {trigger_name} ON {table};
                CREATE TRIGGER {trigger_name}
                    BEFORE UPDATE ON {table}
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """))
        
        # Commit delle modifiche
        conn.commit()


# ==========================================
# UTILITÀ PER PARTITIONING (futuro)
# ==========================================

def create_partitioned_tables(engine):
    """
    Crea tabelle partizionate per trending_snapshots (per data)
    Utile quando i dati crescono molto
    """
    partition_sql = """
    -- Partizionamento per anilist_trending_snapshots per mese
    CREATE TABLE IF NOT EXISTS anilist_trending_snapshots_partitioned (
        LIKE anilist_trending_snapshots INCLUDING ALL
    ) PARTITION BY RANGE (snapshot_date);
    
    -- Partizioni per i prossimi mesi (esempio)
    CREATE TABLE IF NOT EXISTS anilist_trending_snapshots_2024_12 
        PARTITION OF anilist_trending_snapshots_partitioned
        FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');
        
    CREATE TABLE IF NOT EXISTS anilist_trending_snapshots_2025_01
        PARTITION OF anilist_trending_snapshots_partitioned  
        FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
    """
    
    # Implementazione futura quando serve performance


# ==========================================
# EXPORT
# ==========================================

__all__ = [
    'Base',
    'AniListCharacter',
    'AniListMedia', 
    'AniListCharacterMedia',
    'AniListTrendingSnapshot',
    'AniListAggregatedData',
    'AniListSyncLog',
    'AniListServiceConfig',
    'ServiceData',
    'ServiceMetrics',
    'CharacterFavouritesHistory',
    'TrendingConfig',
    'apply_updated_at_triggers',
    'create_partitioned_tables'
]

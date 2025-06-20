"""
Database module for AniList service data persistence
"""
from .database_manager import DatabaseManager
from .schema import (
    Base, AniListCharacter, AniListMedia, AniListCharacterMedia,
    AniListTrendingSnapshot, AniListAggregatedData, AniListSyncLog,
    AniListServiceConfig, ServiceData, ServiceMetrics
)
from .repositories.anilist_character_repository import AniListCharacterRepository

__all__ = [
    'DatabaseManager',
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
    'AniListCharacterRepository'
]

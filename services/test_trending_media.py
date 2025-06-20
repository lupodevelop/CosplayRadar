#!/usr/bin/env python3
"""
Script per testare e popolare il database con serie trending, in uscita e appena uscite
"""
import asyncio
import logging
import json
import sys
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anilist-service'))

async def test_trending_media():
    """Test per fetchare serie trending e in uscita"""
    try:
        from src.fetchers.media_fetcher import MediaFetcher
        from src.models import AniListConfig
        
        config = AniListConfig(database_url="postgresql://fake_url")
        fetcher = MediaFetcher(config)
        
        logger.info("🔥 Fetching trending anime...")
        trending_anime = await fetcher.fetch_trending_anime(limit=10)
        logger.info(f"✅ Trovati {len(trending_anime)} anime trending")
        
        logger.info("📅 Fetching upcoming anime...")
        upcoming_anime = await fetcher.fetch_upcoming_anime(limit=10)
        logger.info(f"✅ Trovati {len(upcoming_anime)} anime in uscita")
        
        logger.info("🆕 Fetching recently released anime...")
        recent_anime = await fetcher.fetch_recently_released_anime(limit=10)
        logger.info(f"✅ Trovati {len(recent_anime)} anime appena usciti")
        
        logger.info("🗓️ Fetching current season anime...")
        current_season = await fetcher.fetch_current_season_anime(limit=10)
        logger.info(f"✅ Trovati {len(current_season)} anime stagione corrente")
        
        # Mostra alcuni risultati
        logger.info("\n🔥 TOP 5 TRENDING ANIME:")
        for i, anime in enumerate(trending_anime[:5], 1):
            logger.info(f"  {i}. {anime.title_romaji} - Trending: {anime.trending_rank}, Pop: {anime.popularity}")
        
        logger.info("\n📅 TOP 5 UPCOMING ANIME:")
        for i, anime in enumerate(upcoming_anime[:5], 1):
            start_date = f"{anime.start_date.get('year', 'TBA')}" if anime.start_date else 'TBA'
            logger.info(f"  {i}. {anime.title_romaji} - Data: {start_date}, Pop: {anime.popularity}")
        
        logger.info("\n🆕 TOP 5 RECENT ANIME:")
        for i, anime in enumerate(recent_anime[:5], 1):
            logger.info(f"  {i}. {anime.title_romaji} - Status: {anime.status}, Pop: {anime.popularity}")
        
        # Conteggia personaggi
        total_characters = 0
        for anime in trending_anime + upcoming_anime + recent_anime:
            total_characters += len(anime.characters)
        
        logger.info(f"\n💫 TOTALE PERSONAGGI RACCOLTI: {total_characters}")
        
        return {
            'trending': trending_anime,
            'upcoming': upcoming_anime,
            'recent': recent_anime,
            'current_season': current_season
        }
        
    except Exception as e:
        logger.error(f"❌ Errore durante il fetch: {e}")
        raise

async def save_trending_data_to_db(media_data):
    """Salva i dati delle serie trending nel database"""
    try:
        import asyncpg
        
        DATABASE_URL = "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev"
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Salva trending anime
        for anime in media_data['trending']:
            try:
                await conn.execute('''
                    INSERT INTO anilist_media (
                        anilist_id, title_romaji, title_english, type, format, status,
                        season, season_year, episodes, genres, popularity, favourites,
                        average_score, trending, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                    ) ON CONFLICT (anilist_id) DO UPDATE SET
                        trending = EXCLUDED.trending,
                        popularity = EXCLUDED.popularity,
                        updated_at = EXCLUDED.updated_at
                ''',
                    anime.id,
                    anime.title_romaji,
                    anime.title_english,
                    anime.type.value,
                    anime.format,
                    anime.status,
                    anime.season,
                    anime.season_year,
                    anime.episodes,
                    anime.genres,
                    anime.popularity,
                    anime.favourites,
                    anime.average_score,
                    anime.trending_rank,
                    datetime.now(),
                    datetime.now()
                )
                
                # Salva personaggi dell'anime
                for character in anime.characters:
                    try:
                        await conn.execute('''
                            INSERT INTO characters (
                                "anilistId", name, series, gender, favourites, media_title, source,
                                "createdAt", "updatedAt"
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9
                            ) ON CONFLICT ("anilistId") DO UPDATE SET
                                favourites = EXCLUDED.favourites,
                                "updatedAt" = EXCLUDED."updatedAt"
                        ''',
                            character.id,
                            character.name_full,
                            anime.title_romaji,
                            character.gender,
                            character.favourites,
                            anime.title_romaji,
                            'anilist_trending',
                            datetime.now(),
                            datetime.now()
                        )
                    except Exception as char_error:
                        logger.warning(f"Errore salvando personaggio {character.name_full}: {char_error}")
                        continue
                        
            except Exception as anime_error:
                logger.warning(f"Errore salvando anime {anime.title_romaji}: {anime_error}")
                continue
        
        await conn.close()
        logger.info("✅ Dati trending salvati nel database")
        
    except Exception as e:
        logger.error(f"❌ Errore salvando nel database: {e}")

async def main():
    """Funzione principale"""
    logger.info("🚀 Avvio test fetching serie trending...")
    
    # Test fetching
    media_data = await test_trending_media()
    
    # Salva nel database
    await save_trending_data_to_db(media_data)
    
    logger.info("✅ Test completato!")

if __name__ == "__main__":
    asyncio.run(main())

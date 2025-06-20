#!/usr/bin/env python3
"""
Script per fetchare dati media da AniList e calcolare trending realistici
Basato sui dati REALI delle serie (status, popolarità, data rilascio)
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json
import asyncpg

# Add the anilist-service to path
sys.path.insert(0, str(Path(__file__).parent.parent / "anilist-service" / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Imports
from fetchers.media_fetcher import MediaFetcher
from fetchers.character_fetcher import CharacterFetcher


class RealisticTrendingCalculator:
    """Calcola trending realistici basati sui dati reali delle serie"""
    
    def __init__(self):
        self.database_url = "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev"
        self.media_fetcher = MediaFetcher()
        self.character_fetcher = CharacterFetcher()
        self.current_year = 2025
        
    async def get_characters_from_db(self):
        """Recupera personaggi dal database con AniList ID"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            characters = await conn.fetch('''
                SELECT id, name, series, "anilistId", favourites, gender, temperature 
                FROM characters 
                WHERE "anilistId" IS NOT NULL 
                ORDER BY favourites DESC
                LIMIT 30
            ''')
            
            logger.info(f"📥 Recuperati {len(characters)} personaggi dal database")
            return characters
            
        finally:
            await conn.close()
    
    async def fetch_media_data_for_character(self, anilist_id):
        """Fetcha i dati della serie associata al personaggio"""
        try:
            # Usa character_fetcher per ottenere il personaggio con media
            character_data = await self.character_fetcher.fetch_character_by_id(anilist_id)
            
            if not character_data or not character_data.media:
                logger.warning(f"❌ Nessun dato media trovato per personaggio {anilist_id}")
                return None
            
            # Prendi il primo anime/manga associato
            media_list = character_data.media
            primary_media = None
            
            # Preferisci anime su manga
            for media in media_list:
                if media.type == "ANIME":
                    primary_media = media
                    break
            
            if not primary_media and media_list:
                primary_media = media_list[0]  # Fallback al primo disponibile
            
            if primary_media:
                # Fetcha dati completi del media
                full_media = await self.media_fetcher.fetch_media_by_id(primary_media.anilist_id)
                return full_media
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Errore fetch media per personaggio {anilist_id}: {e}")
            return None
    
    def calculate_realistic_trending_score(self, character, media_data):
        """Calcola trending score realistico basato sui dati della serie"""
        base_score = min(character['favourites'] / 1000, 100)  # Base 0-100
        
        if not media_data:
            # Nessun dato media, usa score di base
            return {
                'base_score': base_score,
                'status_boost': 1.0,
                'recency_boost': 1.0,
                'popularity_boost': 1.0,
                'type_boost': 1.0,
                'total_boost_multiplier': 1.0,
                'calculated_trending_score': base_score,
                'media_data': None
            }
        
        # ✅ BOOST BASATI SU DATI REALI
        
        # 1. Status boost (serie in corso = più trending)
        status_boost = 1.0
        if media_data.status == "RELEASING":
            status_boost = 1.3  # Serie attualmente in onda
        elif media_data.status == "NOT_YET_RELEASED":
            status_boost = 1.2  # Serie in arrivo (hype)
        elif media_data.status == "FINISHED":
            status_boost = 1.0  # Serie finite
        
        # 2. Recency boost (anni recenti = più trending)
        recency_boost = 1.0
        if media_data.season_year:
            years_ago = self.current_year - media_data.season_year
            if years_ago <= 1:
                recency_boost = 1.25  # Molto recente (2024-2025)
            elif years_ago <= 3:
                recency_boost = 1.15  # Recente (2022-2024)
            elif years_ago <= 5:
                recency_boost = 1.05  # Abbastanza recente (2020-2022)
            else:
                recency_boost = 0.95  # Vecchio (pre-2020)
        
        # 3. Popularity boost (anime popolari = personaggi più trending)
        popularity_boost = 1.0
        if media_data.popularity:
            if media_data.popularity >= 500000:
                popularity_boost = 1.2  # Anime super popolare
            elif media_data.popularity >= 200000:
                popularity_boost = 1.1  # Anime popolare
            elif media_data.popularity >= 100000:
                popularity_boost = 1.05  # Anime conosciuto
        
        # 4. Type boost (TV series = più cosplay di movies)
        type_boost = 1.0
        if media_data.format == "TV":
            type_boost = 1.1  # Serie TV
        elif media_data.format == "MOVIE":
            type_boost = 1.05  # Film
        elif media_data.format in ["OVA", "ONA"]:
            type_boost = 0.95  # OVA/ONA meno mainstream
        
        # 5. Role boost (piccolo boost per supporting characters)
        # TODO: implementare recupero ruolo da media_data.characters
        role_boost = 1.0
        # character_role = getattr(media_data, 'character_role', None)
        # if character_role:
        #     if character_role == "SUPPORTING":
        #         role_boost = 1.05  # Piccolo boost per supporting
        #     elif character_role == "MAIN":
        #         role_boost = 1.0   # Main characters nessun boost extra
        
        # ✅ MOLTIPLICATORE TOTALE (molto più basso!)
        total_multiplier = status_boost * recency_boost * popularity_boost * type_boost * role_boost
        total_multiplier = min(total_multiplier, 1.8)  # Cap a 1.8x massimo
        
        # Score finale
        final_score = base_score * total_multiplier
        
        return {
            'base_score': round(base_score, 2),
            'status_boost': round(status_boost, 3),
            'recency_boost': round(recency_boost, 3),
            'popularity_boost': round(popularity_boost, 3),
            'type_boost': round(type_boost, 3),
            'role_boost': round(role_boost, 3),
            'total_boost_multiplier': round(total_multiplier, 3),
            'calculated_trending_score': round(final_score, 2),
            'media_data': {
                'id': media_data.anilist_id,
                'title': media_data.title_romaji,
                'status': media_data.status,
                'season_year': media_data.season_year,
                'popularity': media_data.popularity,
                'format': media_data.format,
                'mean_score': media_data.mean_score
            }
        }
    
    async def save_trending_to_db(self, character, trending_data):
        """Salva i dati trending nel database"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            await conn.execute('''
                INSERT INTO anilist_trending_snapshots (
                    character_id, snapshot_date, period_type, entity_type,
                    anilist_trending_score, calculated_trending_score,
                    base_score, total_boost_multiplier,
                    recency_boost, quality_boost, gender_boost, role_weight,
                    character_favourites, character_name, character_gender,
                    media_id, media_title, media_format,
                    algorithm_version, calculation_metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
                )
            ''',
            character['anilistId'],                    # character_id
            datetime.now().date(),                     # snapshot_date
            'DAILY',                                   # period_type
            'CHARACTER',                               # entity_type
            0,                                         # anilist_trending_score (non disponibile)
            trending_data['calculated_trending_score'], # calculated_trending_score
            trending_data['base_score'],               # base_score
            trending_data['total_boost_multiplier'],   # total_boost_multiplier
            trending_data['recency_boost'],            # recency_boost
            trending_data['popularity_boost'],         # quality_boost (riutilizziamo)
            trending_data['type_boost'],               # gender_boost (riutilizziamo)
            trending_data['role_boost'],               # role_weight
            character['favourites'],                   # character_favourites
            character['name'],                         # character_name
            character.get('gender'),                   # character_gender
            trending_data['media_data']['id'] if trending_data['media_data'] else None,  # media_id
            trending_data['media_data']['title'] if trending_data['media_data'] else None, # media_title
            trending_data['media_data']['format'] if trending_data['media_data'] else None, # media_format
            '2.0_realistic',                           # algorithm_version
            json.dumps(trending_data)                  # calculation_metadata
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore salvando trending per {character['name']}: {e}")
            return False
        finally:
            await conn.close()
    
    async def process_all_characters(self):
        """Processa tutti i personaggi per calcolare trending realistici"""
        logger.info("🚀 === CALCOLO TRENDING REALISTICI CON DATI MEDIA ===")
        
        # 1. Recupera personaggi dal database
        characters = await self.get_characters_from_db()
        
        # 2. Processa ogni personaggio
        processed = 0
        saved = 0
        
        for char in characters:
            logger.info(f"🎭 Processando {char['name']} (ID: {char['anilistId']})...")
            
            # Fetch dati media
            media_data = await self.fetch_media_data_for_character(char['anilistId'])
            
            # Calcola trending realistico
            trending_data = self.calculate_realistic_trending_score(char, media_data)
            
            # Log risultati
            if media_data:
                logger.info(f"   📺 Serie: {media_data.title_romaji} ({media_data.status}, {media_data.season_year})")
                logger.info(f"   ✅ Score: {trending_data['calculated_trending_score']:.2f} "
                          f"(Base: {trending_data['base_score']:.2f}, Mult: {trending_data['total_boost_multiplier']:.2f}x)")
            else:
                logger.info(f"   ❌ Nessun dato media - Score: {trending_data['calculated_trending_score']:.2f}")
            
            # Salva nel database
            if await self.save_trending_to_db(char, trending_data):
                saved += 1
            
            processed += 1
            
            # Pausa per non sovraccaricare l'API
            await asyncio.sleep(0.5)
        
        logger.info(f"🎉 COMPLETATO! Processati {processed} personaggi, salvati {saved} trending scores")


async def main():
    calculator = RealisticTrendingCalculator()
    await calculator.process_all_characters()


if __name__ == "__main__":
    asyncio.run(main())

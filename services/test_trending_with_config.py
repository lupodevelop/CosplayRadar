#!/usr/bin/env python3
"""
Script per testare trending con configurazione centralizzata
"""
import asyncio
import logging
import json
import asyncpg
import uuid
import sys
import os
from datetime import datetime

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import della configurazione centralizzata
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anilist-service'))

try:
    from trending_config import trending_config
    logger.info("✅ Configurazione centralizzata caricata")
except ImportError as e:
    logger.error(f"❌ Errore import configurazione: {e}")
    # Fallback per test
    class MockConfig:
        def __init__(self):
            self.favourites_divisor = 100
            self.algorithm_version = "v2.4_config"
        
        def get_boost_breakdown(self, **kwargs):
            gender = kwargs.get('gender')
            favourites = kwargs.get('favourites', 0)
            series_name = kwargs.get('series_name', '')
            
            # Replica la logica precedente
            gender_boost = 1.4 if gender == 'Female' else 1.0
            
            popularity_boost = 1.0
            if favourites >= 30000:
                popularity_boost = 1.15
            elif favourites >= 20000:
                popularity_boost = 1.10
            elif favourites >= 10000:
                popularity_boost = 1.05
            
            keywords_boost = 1.0
            if series_name:
                series_lower = series_name.lower()
                if any(kw in series_lower for kw in ['jujutsu', 'one piece', 'demon slayer']):
                    keywords_boost = 1.10
            
            raw_total = gender_boost * popularity_boost * keywords_boost
            capped_total = min(raw_total, 1.3)
            
            return {
                'gender_boost': gender_boost,
                'popularity_boost': popularity_boost,
                'keywords_boost': keywords_boost,
                'status_boost': 1.0,
                'recency_boost': 1.0,
                'format_boost': 1.0,
                'role_boost': 1.0,
                'raw_total': raw_total,
                'capped_total': capped_total
            }
    
    trending_config = MockConfig()
    logger.info("⚠️  Usando configurazione mock")


class TrendingCalculatorWithConfig:
    """Calcola trending usando configurazione centralizzata"""
    
    def __init__(self):
        self.database_url = "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev"
        
    async def get_characters_from_db(self):
        """Recupera personaggi dal database"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            characters = await conn.fetch('''
                SELECT id, name, series, "anilistId", favourites, gender, temperature 
                FROM characters 
                WHERE "anilistId" IS NOT NULL 
                ORDER BY favourites DESC
                LIMIT 10
            ''')
            
            logger.info(f"📥 Recuperati {len(characters)} personaggi dal database")
            return characters
            
        finally:
            await conn.close()
    
    def calculate_trending_score(self, character):
        """Calcola trending score usando configurazione centralizzata"""
        
        # Base score usando configurazione
        favourites = character['favourites']
        base_score = favourites / trending_config.favourites_divisor
        
        # Calcola tutti i boost usando la configurazione
        gender = character.get('gender')
        series_name = character.get('series', '')
        
        # Ottieni breakdown completo dei boost
        boost_breakdown = trending_config.get_boost_breakdown(
            gender=gender,
            favourites=favourites,
            series_name=series_name
        )
        
        # Score finale
        total_multiplier = boost_breakdown['capped_total']
        final_score = base_score * total_multiplier
        
        return {
            'base_score': round(base_score, 2),
            'gender_boost': round(boost_breakdown['gender_boost'], 3),
            'popularity_boost': round(boost_breakdown['popularity_boost'], 3),
            'keywords_boost': round(boost_breakdown['keywords_boost'], 3),
            'status_boost': round(boost_breakdown['status_boost'], 3),
            'recency_boost': round(boost_breakdown['recency_boost'], 3),
            'format_boost': round(boost_breakdown['format_boost'], 3),
            'role_boost': round(boost_breakdown['role_boost'], 3),
            'raw_total_multiplier': round(boost_breakdown['raw_total'], 3),
            'total_boost_multiplier': round(total_multiplier, 3),
            'calculated_trending_score': round(final_score, 2),
            'algorithm_version': trending_config.algorithm_version
        }
    
    async def save_trending_to_db(self, character, trending_data):
        """Salva i dati trending nel database"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            await conn.execute('''
                INSERT INTO anilist_trending_snapshots (
                    id, character_id, snapshot_date, period_type, entity_type,
                    anilist_trending_score, calculated_trending_score,
                    base_score, total_boost_multiplier,
                    recency_boost, quality_boost, gender_boost, role_weight,
                    character_favourites, character_name, character_gender,
                    media_id, media_title, media_format,
                    algorithm_version, calculation_metadata, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
                )
            ''',
            uuid.uuid4(),                              # id (UUID)
            character['anilistId'],                    # character_id
            datetime.now().date(),                     # snapshot_date
            'DAILY',                                   # period_type
            'CHARACTER',                               # entity_type
            0,                                         # anilist_trending_score (non disponibile)
            trending_data['calculated_trending_score'], # calculated_trending_score
            trending_data['base_score'],               # base_score
            trending_data['total_boost_multiplier'],   # total_boost_multiplier
            trending_data['recency_boost'],            # recency_boost
            trending_data['popularity_boost'],         # quality_boost
            trending_data['gender_boost'],             # gender_boost
            trending_data['role_boost'],               # role_weight
            character['favourites'],                   # character_favourites
            character['name'],                         # character_name
            character.get('gender'),                   # character_gender
            None,                                      # media_id (per ora)
            None,                                      # media_title (per ora)
            None,                                      # media_format (per ora)
            trending_data['algorithm_version'],        # algorithm_version
            json.dumps(trending_data),                 # calculation_metadata
            datetime.now()                             # created_at
            )
            
            logger.info(f"💾 Salvato trending per {character['name']}: {trending_data['calculated_trending_score']}")
            
        finally:
            await conn.close()
    
    async def process_all_characters(self):
        """Processa tutti i personaggi"""
        characters = await self.get_characters_from_db()
        
        logger.info(f"🚀 Inizio elaborazione di {len(characters)} personaggi con configurazione centralizzata...")
        
        for i, character in enumerate(characters, 1):
            try:
                logger.info(f"📊 [{i}/{len(characters)}] Elaborazione {character['name']}...")
                
                # Calcola trending score usando configurazione centralizzata
                trending_data = self.calculate_trending_score(character)
                
                # Salva nel database
                await self.save_trending_to_db(character, trending_data)
                
                # Log risultato dettagliato
                logger.info(f"✅ {character['name']}: {trending_data['calculated_trending_score']} " +
                          f"(gender: {trending_data['gender_boost']}x, " +
                          f"popularity: {trending_data['popularity_boost']}x, " +
                          f"total: {trending_data['total_boost_multiplier']}x)")
                
            except Exception as e:
                logger.error(f"❌ Errore elaborazione {character['name']}: {e}")
                continue
        
        logger.info("🎉 Elaborazione completata con configurazione centralizzata!")


async def main():
    """Funzione main"""
    calculator = TrendingCalculatorWithConfig()
    await calculator.process_all_characters()


if __name__ == "__main__":
    print("🚀 Avvio calcolo trending con configurazione centralizzata...")
    asyncio.run(main())

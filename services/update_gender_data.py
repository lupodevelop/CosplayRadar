#!/usr/bin/env python3
"""
Script per aggiornare i dati gender dei personaggi esistenti fetchandoli da AniList
"""
import asyncio
import logging
import sys
import os
import asyncpg
from datetime import datetime

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import da src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anilist-service/src'))

from fetchers.character_fetcher import CharacterFetcher


class GenderUpdater:
    """Aggiorna i dati gender dei personaggi fetchandoli da AniList"""
    
    def __init__(self):
        self.database_url = "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev"
        self.character_fetcher = CharacterFetcher()
        
    async def get_characters_without_gender(self):
        """Recupera personaggi senza gender dal database"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            characters = await conn.fetch('''
                SELECT id, name, "anilistId", gender 
                FROM characters 
                WHERE "anilistId" IS NOT NULL 
                AND (gender IS NULL OR gender = '')
                ORDER BY favourites DESC
                LIMIT 20
            ''')
            
            logger.info(f"📥 Recuperati {len(characters)} personaggi senza gender")
            return characters
            
        finally:
            await conn.close()
    
    async def fetch_character_gender(self, anilist_id):
        """Fetcha i dati del personaggio da AniList per ottenere il gender"""
        try:
            character_data = await self.character_fetcher.fetch_character_by_id(anilist_id)
            
            if character_data and character_data.gender:
                logger.info(f"✅ Gender trovato: {character_data.gender}")
                return character_data.gender
            else:
                logger.warning(f"⚠️  Nessun gender trovato per AniList ID {anilist_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Errore fetch character {anilist_id}: {e}")
            return None
    
    async def update_character_gender(self, character_id, gender):
        """Aggiorna il gender del personaggio nel database"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            await conn.execute('''
                UPDATE characters 
                SET gender = $1 
                WHERE id = $2
            ''', gender, character_id)
            
            logger.info(f"💾 Aggiornato gender per character ID {character_id}: {gender}")
            
        finally:
            await conn.close()
    
    async def process_all_characters(self):
        """Processa tutti i personaggi senza gender"""
        characters = await self.get_characters_without_gender()
        
        logger.info(f"🚀 Inizio aggiornamento gender per {len(characters)} personaggi...")
        
        updated_count = 0
        
        for i, character in enumerate(characters, 1):
            try:
                logger.info(f"📊 [{i}/{len(characters)}] Elaborazione {character['name']} (AniList ID: {character['anilistId']})...")
                
                # 1. Fetch gender da AniList
                gender = await self.fetch_character_gender(character['anilistId'])
                
                if gender:
                    # 2. Aggiorna nel database
                    await self.update_character_gender(character['id'], gender)
                    updated_count += 1
                    
                    logger.info(f"✅ {character['name']}: {gender}")
                else:
                    logger.info(f"⚠️  {character['name']}: gender non disponibile")
                
                # Piccola pausa per non sovraccaricare l'API
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Errore elaborazione {character['name']}: {e}")
                continue
        
        logger.info(f"🎉 Elaborazione completata! Aggiornati {updated_count}/{len(characters)} personaggi")


async def main():
    """Funzione main"""
    updater = GenderUpdater()
    await updater.process_all_characters()


if __name__ == "__main__":
    print("🚀 Avvio aggiornamento gender personaggi...")
    asyncio.run(main())

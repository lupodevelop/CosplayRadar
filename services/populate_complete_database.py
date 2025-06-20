#!/usr/bin/env python3
"""
Script completo per popolare il database con dati AniList e calcolare trending score
Usa la configurazione centralizzata per calcoli realistici e bilanciati
"""
import asyncio
import logging
import json
import asyncpg
import uuid
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the anilist-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anilist-service'))

# Import configurazione centralizzata
try:
    from trending_config import TrendingConfig
    logger.info("✅ Configurazione centralizzata caricata")
except ImportError as e:
    logger.error(f"❌ Errore import configurazione: {e}")
    sys.exit(1)

# Database URL
DATABASE_URL = "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev"

class CompleteDatabasePopulator:
    """Popola il database con dati completi e calcola trending score"""
    
    def __init__(self):
        self.config = TrendingConfig()
        self.database_url = DATABASE_URL
        logger.info(f"🔧 Usando algoritmo versione: {self.config.algorithm_version}")
        
    async def get_characters_from_db(self, limit: int = 50) -> List[Dict]:
        """Recupera personaggi dal database con AniList ID"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            characters = await conn.fetch('''
                SELECT id, name, series, "anilistId", favourites, gender, temperature 
                FROM characters 
                WHERE "anilistId" IS NOT NULL 
                ORDER BY favourites DESC
                LIMIT $1
            ''', limit)
            
            logger.info(f"📥 Recuperati {len(characters)} personaggi dal database")
            return [dict(char) for char in characters]
            
        except Exception as e:
            logger.error(f"❌ Errore recupero personaggi: {e}")
            return []
        finally:
            await conn.close()
    
    async def fetch_character_media_data(self, anilist_id: int) -> Optional[Dict]:
        """Fetcha dati media del personaggio da AniList API"""
        query = '''
        query ($id: Int) {
          Character(id: $id) {
            id
            name {
              full
              first
              last
            }
            gender
            favourites
            media(sort: POPULARITY_DESC, perPage: 5) {
              nodes {
                id
                title {
                  romaji
                  english
                }
                type
                format
                status
                season
                seasonYear
                startDate {
                  year
                  month
                  day
                }
                endDate {
                  year
                  month
                  day
                }
                popularity
                favourites
                meanScore
                genres
                studios {
                  nodes {
                    name
                  }
                }
              }
            }
          }
        }
        '''
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://graphql.anilist.co',
                    json={'query': query, 'variables': {'id': anilist_id}},
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', {}).get('Character')
                    else:
                        logger.warning(f"❌ AniList API error {response.status} per character {anilist_id}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Errore fetch dati per character {anilist_id}: {e}")
            return None
    
    def calculate_base_score(self, favourites: int) -> float:
        """Calcola base score usando configurazione centralizzata"""
        return max(favourites, self.config.min_favourites) / self.config.favourites_divisor
    
    def calculate_trending_score(self, character_data: Dict, media_data: Optional[Dict]) -> Dict[str, Any]:
        """Calcola trending score completo usando configurazione centralizzata"""
        favourites = character_data.get('favourites', 0)
        gender = character_data.get('gender')
        
        # Base score
        base_score = self.calculate_base_score(favourites)
        
        # Determina i parametri per il boost dalla serie più popolare
        boost_params = {
            'gender': gender,
            'favourites': favourites
        }
        
        # Se ci sono dati delle serie, usa la prima (più popolare)
        if media_data and media_data.get('media', {}).get('nodes'):
            main_media = media_data['media']['nodes'][0]  # Prima serie (più popolare)
            
            boost_params.update({
                'status': main_media.get('status'),
                'format': main_media.get('format'),
                'season_year': main_media.get('seasonYear'),
                'series_name': main_media.get('title', {}).get('romaji', '')
            })
        
        # Calcola boost usando configurazione centralizzata
        boost_breakdown = self.config.get_boost_breakdown(**boost_params)
        
        # Calcola score finale
        final_score = round(base_score * boost_breakdown['capped_total'], 3)
        
        return {
            'base_score': round(base_score, 3),
            'final_score': final_score,
            'boost_breakdown': boost_breakdown,
            'character_data': {
                'favourites': favourites,
                'gender': gender
            },
            'calculation_metadata': {
                'algorithm_version': self.config.algorithm_version,
                'calculated_at': datetime.now().isoformat()
            }
        }
    
    async def save_trending_snapshot(self, character: Dict, trending_data: Dict, media_data: Optional[Dict]):
        """Salva snapshot trending nel database"""
        conn = await asyncpg.connect(self.database_url)
        
        try:
            # Prepara dati per snapshot
            character_name = character.get('name', 'Unknown')
            character_id = character.get('id')
            anilist_id = character.get('anilistId')
            
            # Estrai prima serie per riferimento
            series_title = None
            if media_data and media_data.get('media', {}).get('nodes'):
                first_media = media_data['media']['nodes'][0]
                series_title = first_media.get('title', {}).get('romaji', '')
            
            if not series_title:
                series_title = character.get('series', 'Unknown Series')
            
            snapshot_id = str(uuid.uuid4())
            
            await conn.execute('''
                INSERT INTO anilist_trending_snapshots (
                    id, character_id, entity_type, snapshot_date, period_type,
                    calculated_trending_score, base_score, 
                    character_name, character_gender, character_favourites,
                    media_title, calculation_metadata, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                )
            ''', 
                snapshot_id,
                int(character_id),  # Converte a intero
                'character',
                datetime.now().date(),
                'daily',
                round(trending_data['final_score'], 3),
                round(trending_data['base_score'], 3),
                character_name,
                character.get('gender'),
                character.get('favourites'),
                series_title,
                json.dumps(trending_data['calculation_metadata']),
                datetime.now()  # Timestamp corrente per created_at
            )
            
            logger.info(f"💾 Salvato snapshot per {character_name} (score: {trending_data['final_score']:.2f})")
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio snapshot per {character.get('name')}: {e}")
        finally:
            await conn.close()
    
    async def update_character_with_fetched_data(self, character: Dict, media_data: Optional[Dict]):
        """Aggiorna caratteristiche del personaggio con dati fetchati"""
        if not media_data:
            return
            
        conn = await asyncpg.connect(self.database_url)
        
        try:
            character_id = character.get('id')
            
            # Aggiorna gender se disponibile
            new_gender = media_data.get('gender')
            new_favourites = media_data.get('favourites')
            
            updates = []
            values = []
            param_count = 1
            
            if new_gender and new_gender != character.get('gender'):
                updates.append(f"gender = ${param_count}")
                values.append(new_gender)
                param_count += 1
                logger.info(f"🔄 Aggiornamento gender per {character.get('name')}: {new_gender}")
            
            if new_favourites and new_favourites != character.get('favourites'):
                updates.append(f"favourites = ${param_count}")
                values.append(new_favourites)
                param_count += 1
                logger.info(f"🔄 Aggiornamento favourites per {character.get('name')}: {new_favourites}")
            
            if updates:
                values.append(character_id)
                query = f"UPDATE characters SET {', '.join(updates)} WHERE id = ${param_count}"
                await conn.execute(query, *values)
                
        except Exception as e:
            logger.error(f"❌ Errore aggiornamento character {character.get('name')}: {e}")
        finally:
            await conn.close()
    
    async def process_character(self, character: Dict) -> Optional[Dict]:
        """Processa un singolo personaggio: fetch + calcolo + salvataggio"""
        character_name = character.get('name', 'Unknown')
        anilist_id = character.get('anilistId')
        
        logger.info(f"🔄 Processando {character_name} (AniList ID: {anilist_id})")
        
        # Fetch dati da AniList
        media_data = await self.fetch_character_media_data(anilist_id)
        
        if not media_data:
            logger.warning(f"⚠️  Nessun dato AniList per {character_name}")
            # Calcola trending solo con dati locali
            trending_data = self.calculate_trending_score(character, None)
        else:
            # Aggiorna character con dati freschi
            await self.update_character_with_fetched_data(character, media_data)
            
            # Calcola trending con dati completi
            # Merge dati locali con dati AniList
            merged_character = character.copy()
            if media_data.get('gender'):
                merged_character['gender'] = media_data['gender']
            if media_data.get('favourites'):
                merged_character['favourites'] = media_data['favourites']
                
            trending_data = self.calculate_trending_score(merged_character, media_data)
        
        # Salva snapshot
        await self.save_trending_snapshot(character, trending_data, media_data)
        
        return {
            'character': character_name,
            'trending_score': trending_data['final_score'],
            'boost_breakdown': trending_data['boost_breakdown']
        }
    
    async def run_complete_population(self, character_limit: int = 50):
        """Esegue popolazione completa del database"""
        logger.info("🚀 Avvio popolazione completa database...")
        logger.info(f"📊 Configurazione: {self.config.algorithm_version}")
        
        # 1. Recupera personaggi
        characters = await self.get_characters_from_db(character_limit)
        if not characters:
            logger.error("❌ Nessun personaggio trovato nel database")
            return
        
        # 2. Processa ogni personaggio
        results = []
        for i, character in enumerate(characters, 1):
            logger.info(f"📊 Progresso: {i}/{len(characters)}")
            
            try:
                result = await self.process_character(character)
                if result:
                    results.append(result)
                    
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Errore processando {character.get('name')}: {e}")
                continue
        
        # 3. Report finale
        logger.info(f"✅ Processing completato!")
        logger.info(f"📈 Personaggi processati: {len(results)}")
        
        if results:
            # Top 10 trending
            top_trending = sorted(results, key=lambda x: x['trending_score'], reverse=True)[:10]
            
            logger.info("🏆 TOP 10 TRENDING:")
            for i, char in enumerate(top_trending, 1):
                boost_info = char['boost_breakdown']
                logger.info(f"{i:2d}. {char['character']:<25} - Score: {char['trending_score']:6.2f} "
                          f"(Mult: {boost_info.get('capped_total', 1):4.2f}, "
                          f"Gender: {boost_info.get('gender_boost', 1):4.2f})")


async def main():
    """Funzione principale"""
    populator = CompleteDatabasePopulator()
    
    # Esegui popolazione completa
    await populator.run_complete_population(character_limit=30)  # Inizia con 30 personaggi


if __name__ == "__main__":
    # Install aiohttp if needed
    try:
        import aiohttp
    except ImportError:
        logger.error("❌ aiohttp non installato. Installa con: pip install aiohttp")
        sys.exit(1)
    
    asyncio.run(main())

#!/usr/bin/env python3
"""
Script per calcolare e salvare i trending scores nel database
Legge i personaggi dalla tabella characters e calcola i trending scores
"""
import asyncio
import asyncpg
import logging
from datetime import datetime, timedelta
import uuid
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://cosplayradar:dev_password_123@localhost:5432/cosplayradar_dev"

class TrendingCalculator:
    """Calcola trending scores basati su favourites e altri fattori"""
    
    def __init__(self):
        self.algorithm_version = "1.0"
    
    def calculate_base_score(self, favourites):
        """Calcola score di base dai favourites"""
        # Normalizza favourites su scala 0-100
        # Usa logaritmo per dare più peso ai personaggi meno popolari
        import math
        if favourites <= 0:
            return 0
        
        # Formula logaritmica per evitare dominanza dei super popolari
        max_favourites = 50000  # Soglia massima per normalizzazione
        normalized = min(favourites / max_favourites, 1.0)
        
        # Aplica trasformazione logaritmica
        base_score = math.log(1 + normalized * 9) / math.log(10) * 100
        
        return round(base_score, 3)
    
    def calculate_recency_boost(self, last_update):
        """Calcola boost basato su quanto recenti sono i dati"""
        if not last_update:
            return 1.0
        
        days_ago = (datetime.now() - last_update).days
        
        if days_ago <= 1:
            return 1.15  # Molto recente (ridotto da 1.5)
        elif days_ago <= 7:
            return 1.10  # Recente (ridotto da 1.2)
        elif days_ago <= 30:
            return 1.0   # Normale
        else:
            return 0.95  # Vecchio (meno penalizzante)
    
    def calculate_quality_boost(self, character):
        """Calcola boost basato sulla qualità dei dati"""
        boost = 1.0
        
        # Boost per personaggi con AniList ID (ridotto)
        if character.get('anilistId'):
            boost += 0.15  # Ridotto da 0.3
        
        # Boost per descrizione presente (ridotto)
        if character.get('description'):
            boost += 0.10  # Ridotto da 0.2
        
        # Boost per immagine presente (ridotto)
        if character.get('imageUrl'):
            boost += 0.05  # Ridotto da 0.1
        
        # Boost per serie nota (ridotto)
        if character.get('series') and character.get('series') != 'Unknown Series':
            boost += 0.10  # Ridotto da 0.2
        
        return round(boost, 2)
    
    def calculate_gender_boost(self, gender):
        """Calcola boost basato sul gender (per bilanciamento)"""
        if not gender:
            return 1.0
        
        # Leggero boost per personaggi femminili (più cosplayati) - ridotto
        if gender.lower() in ['female', 'f']:
            return 1.05  # Ridotto da 1.1
        elif gender.lower() in ['male', 'm']:
            return 1.0
        else:
            return 1.02  # Non-binary o altro - ridotto da 1.05
    
    def calculate_trending_score(self, character):
        """Calcola il trending score completo"""
        favourites = character.get('favourites', 0)
        
        # Score di base
        base_score = self.calculate_base_score(favourites)
        
        # Boost vari
        recency_boost = self.calculate_recency_boost(character.get('last_temp_update'))
        quality_boost = self.calculate_quality_boost(character)
        gender_boost = self.calculate_gender_boost(character.get('gender'))
        
        # Role weight (assume tutti main character per ora) - ridotto
        role_weight = 1.10  # Ridotto da 1.2
        
        # Calcola moltiplicatore totale
        total_multiplier = recency_boost * quality_boost * gender_boost * role_weight
        
        # Score finale
        trending_score = base_score * total_multiplier
        
        return {
            'base_score': base_score,
            'recency_boost': recency_boost,
            'quality_boost': quality_boost,
            'gender_boost': gender_boost,
            'role_weight': role_weight,
            'total_boost_multiplier': round(total_multiplier, 3),
            'calculated_trending_score': round(trending_score, 3),
            'calculation_metadata': {
                'favourites': favourites,
                'algorithm_version': self.algorithm_version,
                'calculation_date': datetime.now().isoformat(),
                'factors_used': ['favourites', 'recency', 'quality', 'gender', 'role']
            }
        }

async def main():
    """Main function"""
    logger.info("🚀 Avvio calcolo trending scores...")
    
    try:
        # Connessione al database
        conn = await asyncpg.connect(DATABASE_URL)
        logger.info("✅ Connesso al database PostgreSQL")
        
        # Recupera tutti i personaggi AniList
        characters = await conn.fetch("""
            SELECT * FROM characters 
            WHERE "anilistId" IS NOT NULL 
            ORDER BY favourites DESC
        """)
        
        logger.info(f"📊 Trovati {len(characters)} personaggi da processare")
        
        if not characters:
            logger.warning("❌ Nessun personaggio trovato!")
            return
        
        calculator = TrendingCalculator()
        processed = 0
        
        for char in characters:
            try:
                # Converti il record in dict
                character_data = dict(char)
                
                # Calcola trending
                trending_data = calculator.calculate_trending_score(character_data)
                
                # Prepara i dati per l'insert
                record_id = str(uuid.uuid4())
                today = datetime.now().date()
                
                # Insert nella tabella anilist_trending_snapshots
                await conn.execute("""
                    INSERT INTO anilist_trending_snapshots (
                        id, character_id, snapshot_date, entity_type, period_type,
                        anilist_trending_score, calculated_trending_score,
                        base_score, recency_boost, quality_boost, gender_boost,
                        role_weight, total_boost_multiplier, calculation_metadata,
                        character_favourites, character_name, character_gender,
                        media_title, algorithm_version, created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
                    )
                """,
                record_id,
                character_data['anilistId'],  # character_id
                today,  # snapshot_date
                'CHARACTER',  # entity_type
                'DAILY',  # period_type (aggiungo il valore mancante)
                0,  # anilist_trending_score (non disponibile)
                trending_data['calculated_trending_score'],
                trending_data['base_score'],
                trending_data['recency_boost'],
                trending_data['quality_boost'], 
                trending_data['gender_boost'],
                trending_data['role_weight'],
                trending_data['total_boost_multiplier'],
                json.dumps(trending_data['calculation_metadata']),  # metadata come JSON
                character_data['favourites'],
                character_data['name'],
                character_data.get('gender'),
                character_data.get('series'),
                calculator.algorithm_version,
                datetime.now()
                )
                
                processed += 1
                logger.info(f"✅ {character_data['name']}: Score={trending_data['calculated_trending_score']:.2f} (Base: {trending_data['base_score']:.2f}, Mult: {trending_data['total_boost_multiplier']:.2f}x)")
                
            except Exception as e:
                logger.error(f"❌ Errore processando {character_data.get('name', 'Unknown')}: {e}")
                continue
        
        await conn.close()
        
        logger.info(f"🎉 Processo completato! {processed}/{len(characters)} personaggi processati")
        
        # Mostra top 5 trending
        conn = await asyncpg.connect(DATABASE_URL)
        top_trending = await conn.fetch("""
            SELECT character_name, calculated_trending_score, total_boost_multiplier, character_favourites
            FROM anilist_trending_snapshots 
            WHERE snapshot_date = $1
            ORDER BY calculated_trending_score DESC 
            LIMIT 5
        """, today)
        
        logger.info("\n🔥 TOP 5 TRENDING:")
        for i, char in enumerate(top_trending, 1):
            logger.info(f"  {i}. {char['character_name']}: {char['calculated_trending_score']:.2f} (Mult: {char['total_boost_multiplier']:.2f}x, Fav: {char['character_favourites']})")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ Errore generale: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())

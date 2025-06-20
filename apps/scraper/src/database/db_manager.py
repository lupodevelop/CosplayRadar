"""
Database Manager for CosplayRadar Scraper
Handles connections and operations with PostgreSQL database
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, database_url: str = None):
        """Initialize database connection"""
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine)
        logger.info("Database connection initialized")

    def get_connection(self):
        """Get a raw psycopg2 connection"""
        return psycopg2.connect(
            self.database_url,
            cursor_factory=RealDictCursor)

    def upsert_character(
            self, character_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert or update character in database

        Args:
            character_data: Dictionary containing character information

        Returns:
            Dict with 'created' boolean and 'id' of character
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check if character exists
                    cur.execute(
                        "SELECT id FROM characters WHERE name = %s",
                        (character_data['name'],)
                    )
                    existing = cur.fetchone()

                    if existing:
                        # Update existing character
                        update_query = """
                        UPDATE characters SET
                            series = %s,
                            category = %s,
                            popularity = %s,
                            "imageUrl" = %s,
                            description = %s,
                            tags = %s,
                            fandom = %s,
                            gender = %s,
                            "popularityScore" = %s,
                            "sourceUrl" = %s,
                            "updatedAt" = NOW()
                        WHERE id = %s
                        RETURNING id
                        """

                        cur.execute(update_query, (
                            character_data.get('series', 'Unknown'),
                            character_data.get('category', 'OTHER'),
                            character_data.get('popularity', 0.0),
                            character_data.get('imageUrl'),
                            character_data.get('description'),
                            character_data.get('tags', []),
                            character_data.get('fandom', 'Other'),
                            character_data.get('gender', 'Unknown'),
                            character_data.get('popularityScore', 0.0),
                            character_data.get('sourceUrl'),
                            existing['id']
                        ))

                        result = cur.fetchone()
                        conn.commit()

                        return {
                            'created': False,
                            'id': result['id']
                        }

                    else:
                        # Insert new character
                        insert_query = """
                        INSERT INTO characters (
                            name, series, category, popularity, "imageUrl",
                            description, tags, fandom, gender, "popularityScore", "sourceUrl"
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """

                        cur.execute(insert_query, (
                            character_data['name'],
                            character_data.get('series', 'Unknown'),
                            character_data.get('category', 'OTHER'),
                            character_data.get('popularity', 0.0),
                            character_data.get('imageUrl'),
                            character_data.get('description'),
                            character_data.get('tags', []),
                            character_data.get('fandom', 'Other'),
                            character_data.get('gender', 'Unknown'),
                            character_data.get('popularityScore', 0.0),
                            character_data.get('sourceUrl')
                        ))

                        result = cur.fetchone()
                        conn.commit()

                        return {
                            'created': True,
                            'id': result['id']
                        }

        except Exception as e:
            logger.error(
                f"Error upserting character {
                    character_data.get(
                        'name', 'unknown')}: {e}")
            return None

        except Exception as e:
            logger.error(
                f"Error upserting character {
                    character_data.get(
                        'name', 'Unknown')}: {e}")
            return False

    def insert_trend_data(self, trend_data: Dict[str, Any]) -> bool:
        """
        Insert trend data for a character

        Args:
            trend_data: Dictionary containing trend information

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Find character ID
                    cur.execute(
                        "SELECT id FROM characters WHERE name = %s",
                        (trend_data['character_name'],)
                    )
                    character = cur.fetchone()

                    if not character:
                        logger.warning(
                            f"Character not found: {
                                trend_data['character_name']}")
                        return False

                    # Insert trend data
                    insert_query = """
                    INSERT INTO "TrendData" (
                        id, "characterId", platform, mentions, engagement, sentiment, date
                    ) VALUES (
                        gen_random_uuid()::text, %s, %s, %s, %s, %s, %s
                    )
                    """
                    cur.execute(insert_query, (
                        character['id'],
                        trend_data.get('platform', 'REDDIT').upper(),
                        trend_data.get('mentions', 1),
                        trend_data.get('engagement', 0.0),
                        trend_data.get('sentiment', 0.0),
                        trend_data.get('date', datetime.now())
                    ))

                    conn.commit()
                    logger.info(
                        f"Inserted trend data for {
                            trend_data['character_name']}: {
                            trend_data.get(
                                'mentions',
                                1)} mentions")
                    return True

        except Exception as e:
            logger.error(
                f"Error inserting trend data for {
                    trend_data.get(
                        'character_name',
                        'unknown')}: {e}")
            return False

    def get_existing_characters(self) -> List[Dict[str, Any]]:
        """Get all existing characters from database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, name, series, fandom, "popularityScore", "updatedAt"
                        FROM characters
                        ORDER BY "popularityScore" DESC
                    """)
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error fetching existing characters: {e}")
            return []

    def update_popularity_scores(self, decay_factor: float = 0.95) -> bool:
        """
        Apply decay factor to existing popularity scores

        Args:
            decay_factor: Factor to multiply existing scores by (< 1.0 for decay)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE characters
                        SET "popularityScore" = "popularityScore" * %s,
                            "updatedAt" = NOW()
                        WHERE "popularityScore" > 0
                    """, (decay_factor,))

                    conn.commit()
                    logger.info(
                        f"Applied decay factor {decay_factor} to popularity scores")
                    return True

        except Exception as e:
            logger.error(f"Error updating popularity scores: {e}")
            return False

    def map_fandom_to_category(self, fandom: str) -> str:
        """Map fandom type to database category enum"""
        fandom_mapping = {
            'anime': 'ANIME',
            'manga': 'ANIME',
            'game': 'GAMES',
            'games': 'GAMES',
            'gaming': 'GAMES',
            'movie': 'MOVIES',
            'movies': 'MOVIES',
            'film': 'MOVIES',
            'tv': 'TV_SHOWS',
            'television': 'TV_SHOWS',
            'series': 'TV_SHOWS',
            'comic': 'COMICS',
            'comics': 'COMICS',
            'dc': 'COMICS',
            'marvel': 'COMICS'
        }
        return fandom_mapping.get(fandom.lower(), 'OTHER')

    def calculate_difficulty(self, character_data: Dict[str, Any]) -> int:
        """Calculate difficulty score based on character attributes"""
        base_difficulty = 1

        # Simple heuristics for difficulty calculation
        name = character_data.get('name', '').lower()
        series = character_data.get('series', '').lower()
        fandom = character_data.get('fandom', '').lower()

        # Popular/simple characters get lower difficulty
        simple_characters = ['goku', 'naruto', 'luffy', 'pikachu', 'mario']
        if any(char in name for char in simple_characters):
            return 1

        # Complex anime/game characters get higher difficulty
        if 'final fantasy' in series or 'kingdom hearts' in series:
            base_difficulty += 2
        elif fandom in ['anime', 'games']:
            base_difficulty += 1

        # Clamp to 1-5 range
        return min(5, max(1, base_difficulty))

    def generate_character_image_url(self, character_name: str) -> str:
        """Generate character image URL using ui-avatars service"""
        # Create color hash based on character name
        name_hash = hash(character_name) % 16777215  # Get hex color
        color = f"{name_hash:06x}"

        # Get initials
        words = character_name.split()
        initials = ''.join(word[0].upper() for word in words[:2] if word)

        return f"https://ui-avatars.com/api/?name={initials}&background={color}&color=ffffff&size=400"

    def generate_character_tags(
            self, character_data: Dict[str, Any]) -> List[str]:
        """Generate tags for character based on data"""
        tags = []

        fandom = character_data.get('fandom', '').lower()
        series = character_data.get('series', '').lower()

        # Add fandom tag
        if fandom:
            tags.append(fandom)

        # Add series tag
        if series and series != 'unknown':
            tags.append(series)

        # Add popularity tags
        score = character_data.get('popularity_score', 0)
        if score > 80:
            tags.append('trending')
        elif score > 50:
            tags.append('popular')

        # Add platform tag
        tags.append('reddit')

        return list(set(tags))  # Remove duplicates

    def close(self):
        """Close database connections"""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            logger.info("Database connections closed")

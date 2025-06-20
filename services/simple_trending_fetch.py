#!/usr/bin/env python3
"""
Script semplificato per testare il fetching delle serie trending da AniList
"""
import asyncio
import logging
import aiohttp
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleTrendingFetcher:
    """Fetcher semplificato per serie trending"""
    
    def __init__(self):
        self.api_url = "https://graphql.anilist.co"
        
    async def fetch_trending_anime(self, limit=10):
        """Fetch anime trending"""
        query = """
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                }
                media(type: ANIME, sort: TRENDING_DESC) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    type
                    format
                    status
                    startDate {
                        year
                        month
                        day
                    }
                    season
                    seasonYear
                    episodes
                    genres
                    popularity
                    favourites
                    averageScore
                    trending
                    characters(sort: FAVOURITES_DESC, perPage: 10) {
                        edges {
                            role
                            node {
                                id
                                name {
                                    full
                                    native
                                }
                                gender
                                favourites
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'page': 1,
            'perPage': limit
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json={'query': query, 'variables': variables},
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {}).get('Page', {}).get('media', [])
                else:
                    logger.error(f"Error: {response.status}")
                    return []
    
    async def fetch_upcoming_anime(self, limit=10):
        """Fetch upcoming anime"""
        query = """
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                }
                media(type: ANIME, status: NOT_YET_RELEASED, sort: START_DATE) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    type
                    format
                    status
                    startDate {
                        year
                        month
                        day
                    }
                    season
                    seasonYear
                    episodes
                    genres
                    popularity
                    favourites
                    trending
                    averageScore
                    description
                    coverImage {
                        large
                    }
                    studios(isMain: true) {
                        nodes {
                            name
                        }
                    }
                    characters(perPage: 10, sort: [FAVOURITES_DESC]) {
                        nodes {
                            id
                            name {
                                full
                                native
                            }
                            image {
                                large
                            }
                            favourites
                            gender
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'page': 1,
            'perPage': limit
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json={'query': query, 'variables': variables},
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {}).get('Page', {}).get('media', [])
                else:
                    logger.error(f"Error: {response.status}")
                    return []
    
    async def fetch_upcoming_manga(self, limit=10):
        """Fetch upcoming manga"""
        query = """
        query ($page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    hasNextPage
                    currentPage
                }
                media(type: MANGA, status: NOT_YET_RELEASED, sort: START_DATE) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    type
                    format
                    status
                    startDate {
                        year
                        month
                        day
                    }
                    chapters
                    volumes
                    genres
                    popularity
                    favourites
                    trending
                    averageScore
                    description
                    coverImage {
                        large
                    }
                    characters(perPage: 10, sort: [FAVOURITES_DESC]) {
                        nodes {
                            id
                            name {
                                full
                                native
                            }
                            image {
                                large
                            }
                            favourites
                            gender
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'page': 1,
            'perPage': limit
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json={'query': query, 'variables': variables},
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {}).get('Page', {}).get('media', [])
                else:
                    logger.error(f"Error: {response.status}")
                    return []

async def main():
    """Test principale"""
    logger.info("🚀 Test fetching serie trending e in uscita...")
    
    fetcher = SimpleTrendingFetcher()
    
    # Fetch trending anime
    logger.info("🔥 Fetching trending anime...")
    trending = await fetcher.fetch_trending_anime(10)
    logger.info(f"✅ Trovati {len(trending)} anime trending")
    
    # Fetch upcoming anime
    logger.info("📅 Fetching upcoming anime...")
    upcoming = await fetcher.fetch_upcoming_anime(10)
    logger.info(f"✅ Trovati {len(upcoming)} anime in uscita")
    
    # Fetch upcoming manga
    logger.info("📚 Fetching upcoming manga...")
    upcoming_manga = await fetcher.fetch_upcoming_manga(5)
    logger.info(f"✅ Trovati {len(upcoming_manga)} manga in uscita")
    
    # Mostra risultati
    logger.info("\n🔥 TOP 5 TRENDING ANIME:")
    for i, anime in enumerate(trending[:5], 1):
        title = anime.get('title', {}).get('romaji', 'Unknown')
        trending_score = anime.get('trending', 0)
        popularity = anime.get('popularity', 0)
        characters_count = len(anime.get('characters', {}).get('edges', []))
        logger.info(f"  {i}. {title} - Trending: {trending_score}, Pop: {popularity}, Chars: {characters_count}")
    
    logger.info("\n📅 TOP 5 UPCOMING ANIME:")
    for i, anime in enumerate(upcoming[:5], 1):
        title = anime.get('title', {}).get('romaji', 'Unknown')
        start_date = anime.get('startDate', {})
        date_str = f"{start_date.get('year', 'TBA')}"
        popularity = anime.get('popularity', 0)
        characters_count = len(anime.get('characters', {}).get('nodes', []))
        studios = anime.get('studios', {}).get('nodes', [])
        studio_name = studios[0].get('name', 'Unknown') if studios else 'Unknown'
        logger.info(f"  {i}. {title} - Data: {date_str}, Pop: {popularity}, Chars: {characters_count}, Studio: {studio_name}")
    
    logger.info("\n📚 TOP 5 UPCOMING MANGA:")
    for i, manga in enumerate(upcoming_manga[:5], 1):
        title = manga.get('title', {}).get('romaji', 'Unknown')
        start_date = manga.get('startDate', {})
        date_str = f"{start_date.get('year', 'TBA')}"
        popularity = manga.get('popularity', 0)
        characters_count = len(manga.get('characters', {}).get('nodes', []))
        format_type = manga.get('format', 'Unknown')
        logger.info(f"  {i}. {title} - Data: {date_str}, Pop: {popularity}, Chars: {characters_count}, Format: {format_type}")
    
    # Conta personaggi totali
    total_chars = 0
    all_characters = []
    
    # Process trending anime characters (edges.node structure)
    for anime in trending:
        for char_edge in anime.get('characters', {}).get('edges', []):
            char = char_edge.get('node', {})
            if char:
                total_chars += 1
                all_characters.append({
                    'id': char.get('id'),
                    'name': char.get('name', {}).get('full', 'Unknown'),
                    'gender': char.get('gender'),
                    'favourites': char.get('favourites', 0),
                    'anime': anime.get('title', {}).get('romaji', 'Unknown'),
                    'role': char_edge.get('role', 'UNKNOWN'),
                    'type': 'trending'
                })
    
    # Process upcoming anime characters (nodes structure)
    for anime in upcoming:
        for char in anime.get('characters', {}).get('nodes', []):
            if char:
                total_chars += 1
                all_characters.append({
                    'id': char.get('id'),
                    'name': char.get('name', {}).get('full', 'Unknown'),
                    'gender': char.get('gender'),
                    'favourites': char.get('favourites', 0),
                    'anime': anime.get('title', {}).get('romaji', 'Unknown'),
                    'role': 'UNKNOWN',  # Role not available in nodes structure
                    'type': 'upcoming'
                })
    # Process upcoming manga characters (nodes structure)
    for manga in upcoming_manga:
        for char in manga.get('characters', {}).get('nodes', []):
            if char:
                total_chars += 1
                all_characters.append({
                    'id': char.get('id'),
                    'name': char.get('name', {}).get('full', 'Unknown'),
                    'gender': char.get('gender'),
                    'favourites': char.get('favourites', 0),
                    'anime': manga.get('title', {}).get('romaji', 'Unknown'),
                    'role': 'UNKNOWN',  # Role not available in nodes structure
                    'type': 'upcoming_manga'
                })
    
    logger.info(f"\n💫 TOTALE PERSONAGGI RACCOLTI: {total_chars}")
    
    # Top personaggi per popolarità
    sorted_chars = sorted(all_characters, key=lambda x: x['favourites'], reverse=True)
    logger.info("\n⭐ TOP 15 PERSONAGGI PIÙ POPOLARI:")
    for i, char in enumerate(sorted_chars[:15], 1):
        type_emoji = "🔥" if char['type'] == 'trending' else "📅" if char['type'] == 'upcoming' else "📚"
        logger.info(f"  {i}. {char['name']} ({char['anime']}) - {char['favourites']} fav, {char['gender']} {type_emoji}")
    
    return {
        'trending': trending,
        'upcoming': upcoming,
        'upcoming_manga': upcoming_manga,
        'characters': all_characters
    }

if __name__ == "__main__":
    asyncio.run(main())

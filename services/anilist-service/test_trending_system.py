#!/usr/bin/env python3
"""
Test veloce del sistema trending con i nuovi fetcher
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(level=logging.INFO)

async def test_fetchers():
    """Test dei fetcher"""
    print("🧪 Testing fetchers...")
    
    try:
        from fetchers.media_fetcher import MediaFetcher
        from fetchers.upcoming_releases_fetcher import UpcomingReleasesFetcher
        
        print("✅ Imports successful")
        
        # Test MediaFetcher
        media_fetcher = MediaFetcher()
        print("✅ MediaFetcher created")
        
        # Test UpcomingReleasesFetcher  
        upcoming_fetcher = UpcomingReleasesFetcher()
        print("✅ UpcomingReleasesFetcher created")
        
        print("🎉 All fetchers working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_upcoming_anime():
    """Test fetch upcoming anime"""
    try:
        from fetchers.upcoming_releases_fetcher import UpcomingReleasesFetcher
        
        fetcher = UpcomingReleasesFetcher()
        
        print("📥 Fetching upcoming anime...")
        upcoming = await fetcher.fetch_upcoming_anime(months_ahead=2, limit=5)
        
        print(f"✅ Found {len(upcoming)} upcoming anime")
        for anime in upcoming[:3]:
            print(f"  - {anime.title_romaji} ({anime.season} {anime.season_year})")
            
        return True
        
    except Exception as e:
        print(f"❌ Error fetching upcoming: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Testing CosplayRadar Trending System")
        
        # Test 1: Basic fetchers
        if not await test_fetchers():
            return
        
        # Test 2: Upcoming anime
        if not await test_upcoming_anime():
            return
            
        print("🎉 All tests passed!")
    
    asyncio.run(main())

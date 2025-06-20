#!/usr/bin/env python3
"""
Test script for CosplayRadar Python Worker
Tests the connection to database and basic functionality
"""

import os
import sys
from datetime import datetime
import json

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.db_manager import DatabaseManager
from extractors.character_extractor import CharacterExtractor

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        db = DatabaseManager()
        
        # Test simple query
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM characters")
                result = cur.fetchone()
                print(f"✅ Database connection successful! Found {result['count']} characters")
                
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_character_extractor():
    """Test character extraction functionality"""
    print("\n🔍 Testing character extractor...")
    try:
        extractor = CharacterExtractor()
        
        # Test text
        test_text = "I cosplayed as Nezuko from Demon Slayer at the convention! The costume was amazing and everyone loved it."
        
        characters = extractor.extract_characters_from_text(test_text, "test_url")
        
        if characters:
            print(f"✅ Character extractor working! Found {len(characters)} characters:")
            for char in characters:
                print(f"   - {char['name']} (confidence: {char['confidence']:.2f})")
        else:
            print("⚠️  No characters extracted from test text")
            
        return True
    except Exception as e:
        print(f"❌ Character extractor failed: {e}")
        return False

def test_database_operations():
    """Test database insert/update operations"""
    print("\n🔍 Testing database operations...")
    try:
        db = DatabaseManager()
        
        # Test character data
        test_character = {
            'name': 'Test Character',
            'series': 'Test Series',
            'category': 'ANIME',
            'difficulty': 2,
            'popularity': 0.7,
            'imageUrl': db.generate_character_image_url('Test Character'),
            'description': 'A test character for validation',
            'tags': ['test', 'validation'],
            'fandom': 'Test',
            'gender': 'Unknown',
            'popularityScore': 70.0,
            'sourceUrl': 'https://test.com'
        }
        
        # Test upsert
        result = db.upsert_character(test_character)
        
        if result:
            print(f"✅ Character upsert successful! Created: {result.get('created')}, ID: {result.get('id')}")
            
            # Test trend data
            trend_data = {
                'character_name': 'Test Character',
                'platform': 'REDDIT',
                'mentions': 1,
                'engagement': 50.0,
                'sentiment': 0.5,
                'date': datetime.now()
            }
            
            trend_result = db.insert_trend_data(trend_data)
            if trend_result:
                print("✅ Trend data insert successful!")
            else:
                print("⚠️  Trend data insert failed")
                
        else:
            print("❌ Character upsert failed")
            
        return True
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting CosplayRadar Worker Tests")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable not set")
        print("Please check your .env file")
        return
    
    tests = [
        test_database_connection,
        test_character_extractor,
        test_database_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"🏁 Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Worker is ready to run.")
    else:
        print("🔧 Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    main()

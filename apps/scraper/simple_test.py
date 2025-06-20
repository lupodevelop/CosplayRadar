#!/usr/bin/env python3
"""
Simple test for CosplayRadar Worker components
"""

import os
import sys

# Add src directory to path
sys.path.append('src')

def test_imports():
    print("🔍 Testing imports...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ dotenv loaded")
        
        from database.db_manager import DatabaseManager
        print("✅ DatabaseManager imported")
        
        from extractors.character_extractor import CharacterExtractor
        print("✅ CharacterExtractor imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    print("\n🔍 Testing database...")
    
    try:
        from database.db_manager import DatabaseManager
        
        db = DatabaseManager()
        print("✅ Database connection created")
        
        # Test query
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) as count FROM characters")
                result = cur.fetchone()
                print(f"✅ Found {result['count']} characters in database")
        
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_extractor():
    print("\n🔍 Testing character extractor...")
    
    try:
        from extractors.character_extractor import CharacterExtractor
        
        extractor = CharacterExtractor()
        print("✅ CharacterExtractor created")
        
        # Simple test
        test_text = "I love Nezuko from Demon Slayer!"
        characters = extractor.extract_characters_from_text(test_text, "test")
        
        print(f"✅ Extracted {len(characters)} characters from test text")
        for char in characters:
            print(f"   - {char['name']} (confidence: {char.get('confidence', 0):.2f})")
        
        return True
    except Exception as e:
        print(f"❌ Extractor error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing CosplayRadar Worker Components")
    print("=" * 50)
    
    tests = [test_imports, test_database, test_extractor]
    passed = 0
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n🏁 Tests completed: {passed}/{len(tests)} passed")
    if passed == len(tests):
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")

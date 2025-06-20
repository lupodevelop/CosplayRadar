#!/usr/bin/env python3
"""
Test script for AniList service setup
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database.database_manager import DatabaseManager
from src.models import ServiceConfig, DatabaseConfig
from src.utils import setup_logging

async def test_service_setup():
    """Test basic service setup"""
    print("🚀 Testing AniList Service Setup...")
    
    # Setup logging
    setup_logging()
    
    # Test configuration
    print("📋 Testing configuration...")
    try:
        config = ServiceConfig()
        print(f"✅ Configuration loaded: {config.database.type}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test database connection
    print("💾 Testing database connection...")
    try:
        # Use development database settings
        db_config = DatabaseConfig(
            type="postgresql",
            url="postgresql://postgres:postgres@localhost:5432/cosplayradar_dev"
        )
        config.database = db_config
        
        db_manager = DatabaseManager(config)
        
        # Test health check
        health = db_manager.health_check()
        if health['status'] == 'healthy':
            print(f"✅ Database connected: {health}")
        else:
            print(f"❌ Database unhealthy: {health}")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("💡 Make sure Docker database is running:")
        print("   docker-compose up -d db")
        return False
    
    # Test table creation
    print("🗃️  Testing table creation...")
    try:
        db_manager.create_tables()
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"❌ Table creation error: {e}")
        return False
    
    print("🎉 All tests passed! Service is ready.")
    return True

def test_environment():
    """Test environment setup"""
    print("🔍 Checking environment...")
    
    required_dirs = [
        "src",
        "src/fetchers", 
        "src/processors",
        "src/database",
        "src/utils",
        "tests"
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Missing directory: {dir_path}")
            return False
    
    required_files = [
        "requirements.txt",
        "config.example.yaml",
        "main.py",
        "src/models/__init__.py"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ Missing file: {file_path}")
            return False
    
    return True

if __name__ == "__main__":
    print("🧪 AniList Service Test Suite")
    print("=" * 40)
    
    # Test environment first
    if not test_environment():
        print("❌ Environment test failed")
        sys.exit(1)
    
    # Test service setup
    try:
        result = asyncio.run(test_service_setup())
        if result:
            print("\n🎉 All tests passed! 🎉")
            print("\nNext steps:")
            print("1. Copy config.example.yaml to config.yaml")
            print("2. Update database settings in config.yaml")
            print("3. Run: python main.py --mode daily --debug")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

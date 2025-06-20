#!/usr/bin/env python3
"""
Test database connection to CosplayRadar main database
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import psycopg2
    from psycopg2 import sql
    print("✅ psycopg2 available")
except ImportError:
    print("❌ psycopg2 not available. Installing...")
    os.system("pip install psycopg2-binary")

def test_main_db_connection():
    """Test connection to main CosplayRadar database"""
    print("🔍 Testing connection to main CosplayRadar database...")
    
    # Try different common database configurations
    test_configs = [
        {
            'host': 'localhost',
            'port': 5432,
            'database': 'cosplayradar_dev',
            'user': 'cosplayradar',
            'password': 'dev_password_123'
        },
        {
            'host': 'localhost', 
            'port': 5432,
            'database': 'cosplayradar',
            'user': 'cosplayradar',
            'password': 'dev_password_123'
        },
        {
            'host': 'localhost',
            'port': 5432, 
            'database': 'postgres',
            'user': 'cosplayradar',
            'password': 'dev_password_123'
        }
    ]
    
    for i, config in enumerate(test_configs):
        print(f"\n📋 Testing config {i+1}: {config['database']}@{config['host']}")
        
        try:
            conn = psycopg2.connect(**config)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Connected! PostgreSQL version: {version[:50]}...")
            
            # Check if this looks like the CosplayRadar database
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            print(f"📊 Tables found: {len(tables)}")
            
            # Look for CosplayRadar-specific tables
            cosplay_tables = [t for t in tables if any(keyword in t.lower() 
                             for keyword in ['character', 'anime', 'user', 'cosplay'])]
            
            if cosplay_tables:
                print(f"🎭 CosplayRadar tables found: {cosplay_tables[:5]}")
                
                # Check character-like tables
                for table in cosplay_tables:
                    if 'character' in table.lower():
                        cursor.execute(f"SELECT COUNT(*) FROM {table};")
                        count = cursor.fetchone()[0] 
                        print(f"   📈 {table}: {count} records")
                        
                        # Show sample columns
                        cursor.execute(f"""
                            SELECT column_name, data_type 
                            FROM information_schema.columns 
                            WHERE table_name = '{table}' 
                            ORDER BY ordinal_position 
                            LIMIT 5;
                        """)
                        columns = cursor.fetchall()
                        print(f"   📋 Columns: {', '.join([f'{col[0]}({col[1]})' for col in columns])}")
                        
                print(f"🎉 Found CosplayRadar database: {config['database']}")
                
            else:
                print("⚠️  No CosplayRadar-specific tables found")
                if tables:
                    print(f"   Available tables: {tables[:10]}")
            
            cursor.close()
            conn.close()
            
            return config
            
        except psycopg2.Error as e:
            print(f"❌ Connection failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print("\n💡 No database connection successful. Make sure:")
    print("   1. Docker database is running: docker-compose up -d db")
    print("   2. Database is properly initialized")
    print("   3. Check connection parameters in docker-compose.yml")
    
    return None

def check_docker_status():
    """Check if Docker containers are running"""
    print("🐳 Checking Docker status...")
    
    try:
        # Check if docker-compose is available
        result = os.system("docker-compose --version > /dev/null 2>&1")
        if result != 0:
            print("❌ docker-compose not available")
            return False
        
        # Check running containers
        print("📋 Checking running containers...")
        os.system("docker-compose ps")
        
        return True
        
    except Exception as e:
        print(f"❌ Docker check failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 CosplayRadar Database Connection Test")
    print("=" * 50)
    
    # Check Docker first
    check_docker_status()
    print()
    
    # Test database connection
    successful_config = test_main_db_connection()
    
    if successful_config:
        print(f"\n🎉 Success! Use this configuration:")
        print(f"Database: {successful_config['database']}")
        print(f"Host: {successful_config['host']}")
        print(f"Port: {successful_config['port']}")
        print(f"User: {successful_config['user']}")
        
        print(f"\n📝 Update your config.yaml:")
        print(f"""
database:
  development:
    type: postgresql
    host: {successful_config['host']}
    port: {successful_config['port']}
    name: {successful_config['database']}
    user: {successful_config['user']}
    password: {successful_config['password']}
    url: "postgresql://{successful_config['user']}:{successful_config['password']}@{successful_config['host']}:{successful_config['port']}/{successful_config['database']}"
        """.strip())
        
    else:
        print("\n❌ No successful database connection found")
        print("Please check your database setup and try again.")

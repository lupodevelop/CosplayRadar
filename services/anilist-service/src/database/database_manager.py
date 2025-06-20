"""
Database manager for AniList service
Supports development (Docker local) and production (Supabase) environments
"""
import logging
import os
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from .schema import Base, apply_updated_at_triggers
from ..models import ServiceConfig


class DatabaseManager:
    """Manage database connections and sessions"""
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        self.config = config or ServiceConfig()
        self.logger = logging.getLogger(__name__)
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection and session factory"""
        try:
            # Build database URL based on environment
            db_url = self._build_database_url()
            
            # Create engine with appropriate settings
            engine_kwargs = {
                'echo': self.config.database.echo,
                'pool_pre_ping': True,
                'pool_recycle': 3600,  # Recycle connections after 1 hour
            }
            
            # PostgreSQL connection pool settings
            if db_url.startswith('postgresql'):
                engine_kwargs.update({
                    'pool_size': self.config.database.pool_size,
                    'max_overflow': self.config.database.max_overflow,
                    'pool_timeout': 30,
                    'connect_args': {
                        'sslmode': 'require' if 'supabase.co' in db_url else 'prefer',
                        'connect_timeout': 30,
                        'application_name': 'anilist-service'
                    }
                })
            
            self.engine = create_engine(db_url, **engine_kwargs)
            
            # Setup session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Test connection
            self._test_connection()
            
            self.logger.info(f"Database initialized successfully: {self._get_db_info()}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _build_database_url(self) -> str:
        """Build database URL based on environment and configuration"""
        
        # Check for environment-specific URL first
        env_url = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')
        if env_url:
            self.logger.info("Using database URL from environment variable")
            return env_url
        
        # Use configuration-based URL
        if hasattr(self.config.database, 'url') and self.config.database.url:
            return self.config.database.url
        
        # Fallback to development database
        dev_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'name': os.getenv('DB_NAME', 'cosplayradar_dev'),
            'user': os.getenv('DB_USER', 'postgres'),  
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        
        return f"postgresql://{dev_config['user']}:{dev_config['password']}@{dev_config['host']}:{dev_config['port']}/{dev_config['name']}"
    
    def _test_connection(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.logger.info("Database connection test successful")
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            raise
    
    def _get_db_info(self) -> str:
        """Get database connection info for logging (without credentials)"""
        url = str(self.engine.url)
        # Remove password from URL for logging
        if '@' in url:
            parts = url.split('@')
            if len(parts) >= 2:
                credentials = parts[0].split('://')[-1]
                if ':' in credentials:
                    user = credentials.split(':')[0]
                    url = url.replace(credentials, f"{user}:***")
        return url

    def create_tables(self):
        """Create all database tables"""
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Apply PostgreSQL triggers for updated_at
            if self.engine.url.drivername.startswith('postgresql'):
                apply_updated_at_triggers(self.engine)
            
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create database tables: {e}")
            raise

    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            self.logger.info("Database tables dropped successfully")
        except Exception as e:
            self.logger.error(f"Failed to drop database tables: {e}")
            raise

    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def get_session_direct(self) -> Session:
        """Get database session for manual management"""
        return self.SessionLocal()

    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        try:
            with self.get_session() as session:
                # Simple query to test connection
                result = session.execute(text("SELECT 1")).scalar()
                
                # Get basic stats
                stats = self._get_database_stats(session)
                
                return {
                    'status': 'healthy',
                    'connection': 'ok' if result == 1 else 'error',
                    'stats': stats
                }
                
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def _get_database_stats(self, session: Session) -> Dict[str, Any]:
        """Get basic database statistics"""
        try:
            from .schema import AniListCharacter, AniListMedia, AniListTrendingSnapshot, AniListAggregatedData
            
            stats = {}
            
            # Count records in main tables
            stats['characters'] = session.query(AniListCharacter).count()
            stats['media'] = session.query(AniListMedia).count()
            stats['trending_snapshots'] = session.query(AniListTrendingSnapshot).count()
            stats['aggregated_data'] = session.query(AniListAggregatedData).count()
            
            return stats
            
        except Exception as e:
            self.logger.warning(f"Could not get database stats: {e}")
            return {}

    def backup_database(self, backup_path: str = None):
        """Create database backup (SQLite only)"""
        if not self.engine.url.drivername.startswith('sqlite'):
            self.logger.warning("Database backup only supported for SQLite")
            return False
            
        try:
            import shutil
            from datetime import datetime
            
            db_path = str(self.engine.url).replace('sqlite:///', '')
            
            if not backup_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"{db_path}.backup_{timestamp}"
            
            shutil.copy2(db_path, backup_path)
            self.logger.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            return False

    def vacuum_database(self):
        """Vacuum database to reclaim space and optimize"""
        try:
            with self.engine.connect() as conn:
                if self.engine.url.drivername.startswith('sqlite'):
                    conn.execute(text("VACUUM"))
                    self.logger.info("SQLite database vacuumed successfully")
                elif self.engine.url.drivername.startswith('postgresql'):
                    # PostgreSQL VACUUM requires autocommit
                    conn.connection.autocommit = True
                    conn.execute(text("VACUUM ANALYZE"))
                    conn.connection.autocommit = False
                    self.logger.info("PostgreSQL database vacuumed successfully")
                    
        except Exception as e:
            self.logger.error(f"Database vacuum failed: {e}")

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information for monitoring"""
        try:
            info = {
                'driver': self.engine.url.drivername,
                'host': getattr(self.engine.url, 'host', None),
                'port': getattr(self.engine.url, 'port', None),
                'database': getattr(self.engine.url, 'database', None),
                'pool_size': getattr(self.engine.pool, 'size', None),
                'checked_out': getattr(self.engine.pool, 'checkedout', None),
                'overflow': getattr(self.engine.pool, 'overflow', None),
                'checked_in': getattr(self.engine.pool, 'checkedin', None)
            }
            return {k: v for k, v in info.items() if v is not None}
        except Exception as e:
            self.logger.error(f"Could not get connection info: {e}")
            return {}

    def close(self):
        """Close database connections"""
        try:
            if self.engine:
                self.engine.dispose()
                self.logger.info("Database connections closed")
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")

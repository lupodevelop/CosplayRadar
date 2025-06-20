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
from .models import Base
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
                    'max_overflow': 20,
                    'pool_timeout': 30
                })
            
            self.engine = create_engine(db_url, **engine_kwargs)
            
            # Configure session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Add event listeners
            self._setup_event_listeners()
            
            self.logger.info("Database connection initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _build_database_url(self) -> str:
        """Build database URL from configuration"""
        if self.config.database_url:
            return self.config.database_url
        
        # Build from components
        if self.config.database_type == 'sqlite':
            db_path = self.config.database_path or 'data/anilist_service.db'
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return f"sqlite:///{db_path}"
        
        elif self.config.database_type == 'postgresql':
            user = self.config.database_user
            password = self.config.database_password
            host = self.config.database_host
            port = self.config.database_port
            database = self.config.database_name
            
            if not all([user, password, host, database]):
                raise ValueError("Missing required database configuration for PostgreSQL")
            
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        else:
            raise ValueError(f"Unsupported database type: {self.config.database_type}")
    
    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners"""
        if self.config.database_type == 'sqlite':
            # Enable foreign key constraints for SQLite
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables"""
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
                result = session.execute("SELECT 1").scalar()
                
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
            from .models import Character, Media, TrendingScore, HistoricalData
            
            stats = {}
            
            # Count records in main tables
            stats['characters'] = session.query(Character).count()
            stats['media'] = session.query(Media).count()
            stats['trending_scores'] = session.query(TrendingScore).count()
            stats['historical_data'] = session.query(HistoricalData).count()
            
            # Database size (if SQLite)
            if self.config.database_type == 'sqlite':
                db_path = self.config.database_path or 'data/anilist_service.db'
                if os.path.exists(db_path):
                    stats['database_size_mb'] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
            return {'error': str(e)}
    
    def vacuum_database(self):
        """Optimize database (VACUUM for SQLite, ANALYZE for PostgreSQL)"""
        try:
            with self.get_session() as session:
                if self.config.database_type == 'sqlite':
                    session.execute("VACUUM")
                    self.logger.info("SQLite database vacuumed")
                elif self.config.database_type == 'postgresql':
                    session.execute("ANALYZE")
                    self.logger.info("PostgreSQL database analyzed")
                    
        except Exception as e:
            self.logger.error(f"Failed to vacuum database: {e}")
            raise
    
    def backup_database(self, backup_path: str):
        """Create database backup (SQLite only)"""
        if self.config.database_type != 'sqlite':
            raise NotImplementedError("Backup only supported for SQLite databases")
        
        try:
            import shutil
            
            db_path = self.config.database_path or 'data/anilist_service.db'
            
            # Ensure backup directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy database file
            shutil.copy2(db_path, backup_path)
            
            self.logger.info(f"Database backed up to {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            raise
    
    def close(self):
        """Close database connections"""
        try:
            if self.engine:
                self.engine.dispose()
                self.logger.info("Database connections closed")
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

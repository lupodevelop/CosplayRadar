"""
Utility funct    # Create log directory if needed
    actual_log_file = log_file or 'logs/anilist_service.log'
    log_dir = os.path.dirname(actual_log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(actual_log_file)
        ]
    )t service
"""
import logging
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml

from ..models import AniListConfig


def setup_logging(level: str = 'INFO', log_file: Optional[str] = None):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper())
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file or 'logs/anilist_service.log')
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)


def load_config(config_path: Optional[str] = None) -> AniListConfig:
    """Load configuration from file or environment variables"""
    config_data = {}
    
    # Try to load from file
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                config_data = yaml.safe_load(f)
            else:
                config_data = json.load(f)
    
    # Override with environment variables
    env_mapping = {
        'DATABASE_URL': 'database_url',
        'DATABASE_TYPE': 'database_type',
        'DATABASE_HOST': 'database_host',
        'DATABASE_PORT': 'database_port',
        'DATABASE_NAME': 'database_name',
        'DATABASE_USER': 'database_user',
        'DATABASE_PASSWORD': 'database_password',
        'DATABASE_PATH': 'database_path',
        'TRENDING_ANIME_LIMIT': 'trending_anime_limit',
        'TRENDING_MANGA_LIMIT': 'trending_manga_limit',
        'POPULAR_CHARACTERS_LIMIT': 'popular_characters_limit',
        'FEMALE_BOOST': 'female_boost',
        'MALE_BOOST': 'male_boost',
        'DAILY_RETENTION_DAYS': 'daily_retention_days',
        'WEEKLY_RETENTION_WEEKS': 'weekly_retention_weeks',
        'MONTHLY_RETENTION_MONTHS': 'monthly_retention_months',
        'YEARLY_RETENTION_YEARS': 'yearly_retention_years'
    }
    
    for env_var, config_key in env_mapping.items():
        env_value = os.getenv(env_var)
        if env_value:
            # Convert to appropriate type
            if config_key.endswith('_limit') or config_key.endswith('_days') or \
               config_key.endswith('_weeks') or config_key.endswith('_months') or \
               config_key.endswith('_years') or config_key.endswith('_port'):
                config_data[config_key] = int(env_value)
            elif config_key.endswith('_boost'):
                config_data[config_key] = float(env_value)
            else:
                config_data[config_key] = env_value
    
    return AniListConfig(**config_data)


def load_config(config_path: str = "config.yaml"):
    """Load service configuration from YAML file"""
    from ..models import ServiceConfig
    
    try:
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        # Create a flattened config for ServiceConfig
        flat_config = {}
        
        # Database configuration
        if 'database' in config_dict:
            db_config = config_dict['database']
            if 'development' in db_config:
                flat_config['database'] = db_config['development']
            else:
                flat_config['database'] = db_config
        
        # AniList configuration
        if 'anilist' in config_dict:
            anilist_config = config_dict['anilist']
            flat_config['anilist'] = {
                'api_url': anilist_config.get('base_url', 'https://graphql.anilist.co'),
                'rate_limit_per_minute': anilist_config.get('rate_limit', 90),
                'request_timeout': anilist_config.get('timeout', 30),
                'database_url': flat_config.get('database', {}).get('url', ''),
            }
        
        # Sync configuration
        if 'sync' in config_dict:
            sync_config = config_dict['sync']
            flat_config.update({
                'character_batch_size': sync_config.get('character_batch_size', 100),
                'media_batch_size': sync_config.get('media_batch_size', 50),
                'full_sync_character_limit': sync_config.get('full_sync_character_limit', 1000),
                'daily_sync_character_limit': sync_config.get('daily_sync_character_limit', 200),
                'character_data_max_age': sync_config.get('character_data_max_age', 168),
                'skip_update_threshold': sync_config.get('skip_update_threshold', 0.05),
            })
        
        # Logging configuration
        if 'logging' in config_dict:
            log_config = config_dict['logging']
            flat_config.update({
                'log_level': log_config.get('level', 'INFO'),
                'log_format': log_config.get('format', 'structured'),
            })
        
        return ServiceConfig(**flat_config)
        
    except FileNotFoundError:
        logging.warning(f"Configuration file {config_path} not found, using defaults")
        return ServiceConfig()
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return ServiceConfig()


def ensure_directories():
    """Ensure required directories exist"""
    directories = [
        'data',
        'logs',
        'backups'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def validate_config(config: AniListConfig) -> List[str]:
    """Validate configuration and return list of errors"""
    errors = []
    
    # Database validation
    if config.database_type not in ['sqlite', 'postgresql']:
        errors.append(f"Unsupported database type: {config.database_type}")
    
    if config.database_type == 'postgresql':
        required_fields = ['database_host', 'database_name', 'database_user', 'database_password']
        for field in required_fields:
            if not getattr(config, field):
                errors.append(f"Missing required PostgreSQL config: {field}")
    
    # Limits validation
    if config.trending_anime_limit <= 0:
        errors.append("trending_anime_limit must be positive")
    
    if config.trending_manga_limit <= 0:
        errors.append("trending_manga_limit must be positive")
    
    if config.popular_characters_limit <= 0:
        errors.append("popular_characters_limit must be positive")
    
    # Boost validation
    if config.female_boost < 0 or config.male_boost < 0:
        errors.append("Gender boosts must be non-negative")
    
    # Retention validation
    if config.daily_retention_days <= 0 or config.weekly_retention_weeks <= 0 or \
       config.monthly_retention_months <= 0 or config.yearly_retention_years <= 0:
        errors.append("All retention periods must be positive")
    
    return errors


def create_sample_config(file_path: str = 'config.yaml'):
    """Create a sample configuration file"""
    sample_config = {
        'database': {
            'type': 'sqlite',
            'path': 'data/anilist_service.db',
            'echo': False
        },
        'limits': {
            'trending_anime_limit': 50,
            'trending_manga_limit': 50,
            'popular_characters_limit': 200
        },
        'boosts': {
            'female_boost': 1.2,
            'male_boost': 1.0,
            'gender_boost_weight': 0.15,
            'recency_boost_weight': 0.2,
            'quality_boost_weight': 0.25,
            'role_weight_factor': 0.3
        },
        'retention': {
            'daily_retention_days': 30,
            'weekly_retention_weeks': 24,
            'monthly_retention_months': 12,
            'yearly_retention_years': 5
        }
    }
    
    with open(file_path, 'w') as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)
    
    print(f"Sample configuration created at {file_path}")


def calculate_estimated_storage(config: AniListConfig) -> Dict[str, Any]:
    """Calculate estimated storage requirements"""
    # Average sizes per record (in bytes)
    character_size = 2048  # JSON data, images URLs, etc.
    media_size = 3072      # More detailed data
    trending_score_size = 512
    historical_data_size = 256
    
    # Estimate daily records
    daily_characters = config.popular_characters_limit
    daily_media = config.trending_anime_limit + config.trending_manga_limit
    daily_trending_scores = daily_characters + daily_media
    daily_historical = daily_trending_scores
    
    # Calculate storage for different periods
    daily_storage = (
        daily_characters * character_size +
        daily_media * media_size +
        daily_trending_scores * trending_score_size +
        daily_historical * historical_data_size
    )
    
    # Account for retention policies
    total_daily_records = daily_storage * config.daily_retention_days
    total_weekly_records = (daily_historical * 7) * config.weekly_retention_weeks
    total_monthly_records = (daily_historical * 30) * config.monthly_retention_months
    total_yearly_records = (daily_historical * 365) * config.yearly_retention_years
    
    total_estimated = (
        total_daily_records +
        total_weekly_records +
        total_monthly_records +
        total_yearly_records
    )
    
    return {
        'daily_size': format_file_size(daily_storage),
        'estimated_total': format_file_size(total_estimated),
        'breakdown': {
            'characters': format_file_size(daily_characters * character_size * config.daily_retention_days),
            'media': format_file_size(daily_media * media_size * config.daily_retention_days),
            'trending_scores': format_file_size(daily_trending_scores * trending_score_size * config.daily_retention_days),
            'historical_data': format_file_size(total_weekly_records + total_monthly_records + total_yearly_records)
        }
    }


def health_check_system() -> Dict[str, Any]:
    """Perform system health check"""
    import psutil
    import platform
    
    health = {
        'system': {
            'platform': platform.system(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total': format_file_size(psutil.virtual_memory().total),
            'memory_available': format_file_size(psutil.virtual_memory().available),
            'disk_free': format_file_size(psutil.disk_usage('.').free)
        },
        'directories': {}
    }
    
    # Check required directories
    for directory in ['data', 'logs', 'backups']:
        if os.path.exists(directory):
            health['directories'][directory] = 'exists'
        else:
            health['directories'][directory] = 'missing'
    
    return health

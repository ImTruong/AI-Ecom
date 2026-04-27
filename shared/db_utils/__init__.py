"""Database utilities"""
import os


def get_database_config(service_name: str) -> dict:
    """
    Get database configuration for a service
    
    Args:
        service_name: Name of the service (auth, customer, staff)
    
    Returns:
        Database configuration dictionary
    """
    database_url = os.getenv(f'{service_name.upper()}_DATABASE_URL')
    
    if database_url:
        # Parse DATABASE_URL (postgresql://user:pass@host:port/db)
        import re
        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, database_url)
        
        if match:
            user, password, host, port, db_name = match.groups()
            return {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_name,
                'USER': user,
                'PASSWORD': password,
                'HOST': host,
                'PORT': port,
            }
    
    # Fallback to individual env vars
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv(f'{service_name.upper()}_DB_NAME', f'{service_name}_db'),
        'USER': os.getenv(f'{service_name.upper()}_DB_USER', f'{service_name}_user'),
        'PASSWORD': os.getenv(f'{service_name.upper()}_DB_PASSWORD', f'{service_name}_pass'),
        'HOST': os.getenv(f'{service_name.upper()}_DB_HOST', 'localhost'),
        'PORT': os.getenv(f'{service_name.upper()}_DB_PORT', '5432'),
    }

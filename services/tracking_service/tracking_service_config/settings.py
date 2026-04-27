import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-tracking-service-key'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'tracking_app',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'tracking_service_config.urls'

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://tracking_user:tracking_pass@tracking_db:5432/tracking_db')

# Parse DATABASE_URL (support both postgres:// and postgresql://)
import re
pattern = r'postgres(?:ql)?://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
match = re.match(pattern, DATABASE_URL)

if match:
    user, password, host, port, db_name = match.groups()
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': user,
            'PASSWORD': password,
            'HOST': host,
            'PORT': port,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

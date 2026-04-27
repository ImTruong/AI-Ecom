import os
import sys
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Add shared libraries to path
SHARED_DIR = os.path.join(BASE_DIR.parent.parent, 'shared')
sys.path.insert(0, SHARED_DIR)

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-supplier-dev-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'supplier_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'supplier_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'supplier_service.wsgi.application'

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://supplier_user:supplier_pass@supplier_db:5432/supplier_db')

import re
pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
JWT_ALGORITHM = 'HS256'

CORS_ALLOW_ALL_ORIGINS = True

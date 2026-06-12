from pathlib import Path
from datetime import timedelta
import sys
import dj_database_url

from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

def env_bool(name, default=False):
    value = config(name, default=default)
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on", "debug", "development", "dev"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off", "release", "prod", "production"}:
        return False
    return default

# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')
DEBUG = env_bool('DEBUG', default=False)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='127.0.0.1,localhost',
    cast=Csv(),
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    # Local apps
    'users',
    'placements',
    'logbook',
    'dashboards',
    'reviews',
    'apps.core',
]

AUTH_USER_MODEL = 'users.CustomUser'

# iles_backend/settings.py

MIDDLEWARE = [
    # CorsMiddleware MUST be first — it needs to handle preflight
    # requests before Django touches them
    'corsheaders.middleware.CorsMiddleware',
    # Django's core security checks (HTTPS, HSTS, etc.)
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serves your static files in production
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # Enables sessions (needed for Django admin)
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Handles common HTTP tasks (URL slashes, content type)
    'django.middleware.common.CommonMiddleware',
    # Protects against Cross-Site Request Forgery attacks
    'django.middleware.csrf.CsrfViewMiddleware',
    # Reads the JWT and attaches request.user
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Enables flash messages in templates
    'django.contrib.messages.middleware.MessageMiddleware',
    # Prevents your app from being embedded in iframes (clickjacking)
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
db_engine = config('DB_ENGINE', default='django.db.backends.sqlite3')
DATABASE_URL = config('DATABASE_URL', default='')

if 'test' in sys.argv:
    # Fast SQLite for running tests locally
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'test_db.sqlite3',
        }
    }
elif DATABASE_URL:
    # Production — Render/Supabase provides a single connection URL
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,        # reuse connections for 10 mins
            conn_health_checks=True, # drop unhealthy connections automatically
        )
    }
else:
    # Local development — reads separate vars from .env
    db_engine = config('DB_ENGINE', default='django.db.backends.sqlite3')
    if db_engine == 'django.db.backends.sqlite3':
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': config('DB_NAME', default=str(BASE_DIR / 'db.sqlite3')),
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': config('DB_ENGINE'),
                'NAME': config('DB_NAME'),
                'USER': config('DB_USER'),
                'PASSWORD': config('DB_PASSWORD'),
                'HOST': config('DB_HOST', default='127.0.0.1'),
                'PORT': config('DB_PORT', default=5432, cast=int),
            }
        }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173',
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
        'login': '10/minute',
        'register': '50/hour',
    },
    'EXCEPTION_HANDLER': 'api.error_handlers.custom_exception_handler',
}


SPECTACULAR_SETTINGS = {
"TITLE": "ILES Backend API",
"DESCRIPTION": "API documentation for the ILES Backend, built with Django REST Framework and drf-spectacular.",
"VERSION": "1.0.0",

}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', default=True)
EMAIL_USE_SSL = env_bool('EMAIL_USE_SSL', default=False)
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=20, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='apikey')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
_EMAIL_PLACEHOLDERS = {'', 'your-email@gmail.com', 'your-email@example.com', 'your-app-password'}
EMAIL_CREDENTIALS_CONFIGURED = bool(
    EMAIL_HOST_PASSWORD and EMAIL_HOST_PASSWORD not in _EMAIL_PLACEHOLDERS)

_CONFIGURED_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='').strip()
DEFAULT_FROM_EMAIL = (
    _CONFIGURED_FROM_EMAIL
    if _CONFIGURED_FROM_EMAIL and 'your-email@gmail.com' not in _CONFIGURED_FROM_EMAIL
    else 'ILES System <sserunkuumajoshua641@gmail.com>'
)
EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default=(
        'django.core.mail.backends.smtp.EmailBackend'
        if EMAIL_CREDENTIALS_CONFIGURED
        else 'django.core.mail.backends.console.EmailBackend'
    ),
)

FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')
FRONTEND_PASSWORD_RESET_PATH = config('FRONTEND_PASSWORD_RESET_PATH', default='/reset-password')

if not DEBUG:
    # Force all HTTP traffic to redirect to HTTPS
    # Render provides HTTPS automatically — this ensures no one
    # accidentally connects over plain HTTP
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    # Apply HSTS to all subdomains too
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # Allow this site to be added to browser HSTS preload lists
    SECURE_HSTS_PRELOAD = True
    # Session cookie only travels over HTTPS, never plain HTTP
    SESSION_COOKIE_SECURE = True
    # CSRF cookie only travels over HTTPS, never plain HTTP
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

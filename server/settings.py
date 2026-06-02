import os
from datetime import timedelta
from pathlib import Path
import environ

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()  

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Core Settings
# -----------------------------------------------------------------------------
SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

BACKEND_BASE_URL = env("BACKEND_BASE_URL", default="http://localhost:8000")
FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="http://localhost:5173")

# -----------------------------------------------------------------------------
# Application Definition
# -----------------------------------------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.product",
    "apps.orders",
    "apps.payments",
    "apps.contact",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.gzip.GZipMiddleware",
]

ROOT_URLCONF = 'server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'server.wsgi.application'

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        "CONN_MAX_AGE": 60,
    }
}

# -----------------------------------------------------------------------------
# REST Framework Configuration
# -----------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 10,
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
}

# -----------------------------------------------------------------------------
# JWT Configuration
# -----------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30), 
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# -----------------------------------------------------------------------------
# Auth / OTP Settings
# -----------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

OTP_LENGTH = 6
OTP_VERIFY_WINDOW_SECONDS = 60
OTP_MAX_RESEND = 3
PASSWORD_RESET_EXPIRY_MINUTES = 10

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
        "queue": {
            "class": "logging.handlers.QueueHandler",
            "queue": "ext://apps.core.logging._log_queue",
        },
    },
    "root": {
        "handlers": ["console"], 
        "level": "INFO",
    },
}

# -----------------------------------------------------------------------------
# Static & Media
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Image Upload Limit (1MB = 1024 * 1024 bytes)
DATA_UPLOAD_MAX_MEMORY_SIZE = 1048576 
FILE_UPLOAD_MAX_MEMORY_SIZE = 1048576

# -----------------------------------------------------------------------------
# Security & CORS
# -----------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    FRONTEND_BASE_URL,
]
CORS_ALLOW_CREDENTIALS = True

# যদি উপরের কাজ না করে, তাহলে টেস্টিংয়ের জন্য:
CORS_ALLOW_ALL_ORIGINS = True  # শুধু ডেভেলপমেন্টে, প্রোডাকশনে REMOVE

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# -----------------------------------------------------------------------------
# Email Settings
# -----------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "smtp.gmail.com"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = f"Shaistaganj E-shop <{EMAIL_HOST_USER}>"

# -----------------------------------------------------------------------------
# Google OAuth Settings
# -----------------------------------------------------------------------------
GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID')  
GOOGLE_CLIENT_SECRET = env('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = env('GOOGLE_REDIRECT_URI')
FRONTEND_BASE_URL = env('FRONTEND_BASE_URL')

SITE_ID = 1
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
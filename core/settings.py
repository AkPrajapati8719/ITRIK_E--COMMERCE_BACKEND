import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

# =============================================================================
# BASE
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-dev-key-change-in-production"
)

DEBUG = os.getenv("DEBUG", "True") == "True"

# 🔥 FIX 1: Removed os.getenv split, removed https://, and used a clean list.
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "itrik-e-commerce-backend-1.onrender.com",
    ".vercel.app",  # Optional: Allows any Vercel preview branch to communicate
    ".onrender.com", # Optional:
]

# =============================================================================
# GOOGLE AUTH
# =============================================================================
# GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# =============================================================================
# INSTALLED APPS
# =============================================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",

    # Local apps
    "accounts.apps.AccountsConfig",
    "store.apps.StoreConfig",
    "cart.apps.CartConfig",
    "orders.apps.OrdersConfig",
    "content.apps.ContentConfig",
]

# =============================================================================
# MIDDLEWARE
# =============================================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",           # 1. Handle CORS first
    "django.middleware.security.SecurityMiddleware",    # 2. Security second
    "whitenoise.middleware.WhiteNoiseMiddleware",      # ✅ UPDATED: Added for static files
    "django.contrib.sessions.middleware.SessionMiddleware", # 3. Sessions third
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

# =============================================================================
# TEMPLATES
# =============================================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# =============================================================================
# DATABASE
# =============================================================================
DATABASES = {
    'default': dj_database_url.config(
        # This will use the DATABASE_URL environment variable on Render
        # If working locally, it falls back to your local SQLite file
        default=os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600
    )
}

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC & MEDIA
# =============================================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Left exactly as you requested
STATICFILES_DIRS = [
    BASE_DIR.parent / "frontend_Itrik_code" / "static",
]

# ✅ UPDATED: Storage for WhiteNoise to handle Admin CSS/JS on Render
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =============================================================================
# CUSTOM USER MODEL
# =============================================================================
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        # "rest_framework.permissions.IsAuthenticated",
        "rest_framework.permissions.AllowAny",
    ),
}

# =============================================================================
# JWT CONFIGURATION
# =============================================================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# =============================================================================
# EMAIL CONFIGURATION (REAL OTP EMAIL)
# =============================================================================

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

# ✅ IMPORTANT FIX
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER

# =============================================================================
# FAST2SMS GATEWAY CONFIG (PRODUCTION READY)
# =============================================================================

# Change to True when you are ready to send real text messages
FAST2SMS_ENABLED = os.getenv("FAST2SMS_ENABLED", "False").lower() == "true"

# Your Fast2SMS API Key from the .env file
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "").strip()

# Fail-safe (prevents server from crashing silently if key is missing in production)
if FAST2SMS_ENABLED and not FAST2SMS_API_KEY:
    raise RuntimeError("🚨 FAST2SMS is enabled but FAST2SMS_API_KEY is missing in your .env file!")
    
# =============================================================================
# RAZORPAY PAYMENT CONFIG
# =============================================================================

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

# =============================================================================
# OTP CONFIG
# =============================================================================
OTP_EXPIRY_MINUTES = 5
OTP_LENGTH = 6
OTP_ATTEMPT_LIMIT = 5

# =============================================================================
# CORS
# =============================================================================
# CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# 🔥 FIX 2: Added https:// to the Vercel link, and included local ports for testing.
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://itrik-e-commerce-frontend.vercel.app", 
]

# =============================================================================
# LOGGING
# =============================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# SECURITY FIXES (REQUIRED)
# =============================================================================

from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = list(default_headers) + [
    "authorization",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://itrik-e-commerce-frontend.vercel.app", 
    "https://itrik-e-commerce-backend-1.onrender.com", 
]

# =============================================================================
# Session and cookies  (CART + ORDER)
# =============================================================================

SESSION_ENGINE = "django.contrib.sessions.backends.db"

# 🔴 CRITICAL FOR VERCEL + RENDER (Cross-Domain)
SESSION_COOKIE_SAMESITE = "None"
CSRF_COOKIE_SAMESITE = "None"
SESSION_SAVE_EVERY_REQUEST = True

# Dev vs Production handling
if DEBUG:
    SESSION_COOKIE_SAMESITE = "Lax"  # Changed from "None"
    CSRF_COOKIE_SAMESITE = "Lax"     # Changed from "None"
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SESSION_COOKIE_SAMESITE = "None" # Keep "None" for Production (HTTPS)
    CSRF_COOKIE_SAMESITE = "None"    # Keep "None" for Production (HTTPS)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
"""
Production settings for HOREMOW backend.
Enforces fail-closed security, TLS, strict CORS, and security headers.
"""

import os

from .base import *

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False

ALLOWED_HOSTS = [host.strip() for host in os.environ["ALLOWED_HOSTS"].split(",") if host.strip()]

# Strict CORS Allowlist
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.environ["CORS_ALLOWED_ORIGINS"].split(",") if origin.strip()]
CORS_ALLOW_CREDENTIALS = True

# Production Database must be PostgreSQL
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    raise ValueError("Production requires a valid PostgreSQL DATABASE_URL, not SQLite.")

# Strict SSL & Transport Security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Secure Cookie Policies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SAMESITE = "Strict"

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Production Static Files (WhiteNoise)
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

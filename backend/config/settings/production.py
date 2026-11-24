"""
Production settings for HOREMOW backend.
Enforces fail-closed security, TLS, strict CORS, and security headers.
"""

import os

from .base import *

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False

raw_hosts = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [host.strip() for host in raw_hosts.split(",") if host.strip()]

# Auto-detect Render external hostname and allow onrender.com subdomains
render_external_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_external_hostname and render_external_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_external_hostname)

# Always allow .onrender.com wildcards on Render deployments
if os.environ.get("RENDER") or any("onrender.com" in h for h in ALLOWED_HOSTS) or not ALLOWED_HOSTS:
    if ".onrender.com" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(".onrender.com")

# Strict CORS Allowlist
CORS_ALLOW_ALL_ORIGINS = False
raw_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
CORS_ALLOW_CREDENTIALS = True

# CSRF Trusted Origins (required for Django 4+ HTTPS requests)
raw_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in raw_csrf.split(",") if origin.strip()]
for origin in CORS_ALLOWED_ORIGINS:
    if origin.startswith("http") and origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

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

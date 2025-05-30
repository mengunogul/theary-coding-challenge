"""
Django settings for the Theary coding challenge project.

This module contains all configuration settings for the Django application,
including database configuration, installed apps, middleware, and logging setup.

Environment Variables:
    SECRET_KEY: Django secret key for cryptographic signing
    DEBUG: Enable/disable debug mode (default: True)
    ALLOWED_HOSTS: Comma-separated list of allowed hostnames
    DB_NAME: PostgreSQL database name
    DB_USER: PostgreSQL database user
    DB_PASSWORD: PostgreSQL database password
    DB_HOST: PostgreSQL database host
    DB_PORT: PostgreSQL database port

Key Features:
    - PostgreSQL database configuration
    - Structured logging with structlog
    - DRF Spectacular for API documentation
    - Async support with ADRF
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import structlog

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
# override=False ensures existing environment variables take precedence
load_dotenv(BASE_DIR.parent / ".env", override=False)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

APPEND_SLASH = True

# Application definition
INSTALLED_APPS = [
    # Django core applications
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party applications
    "drf_spectacular",  # API documentation
    "adrf",  # Async Django REST Framework
    # Local applications
    "api.tree",  # Tree management API
]

# Django REST Framework configuration
REST_FRAMEWORK = {
    # Use drf-spectacular for OpenAPI schema generation
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# API documentation configuration
SPECTACULAR_SETTINGS = {
    "TITLE": "Theary Coding Challenge API",
    "DESCRIPTION": "Theary Coding Challenge",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "theary.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "theary.asgi.application"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Use in-memory SQLite database for development testing to avoid external DB dependencies
if os.environ.get("ENVIRONMENT", "dev") == "dev":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", ""),
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", ""),
            "PORT": os.getenv("DB_PORT", ""),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Structured logging configuration using structlog
# Provides consistent, structured log output with JSON formatting in production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            # Use console renderer in debug mode, JSON in production
            "processor": structlog.dev.ConsoleRenderer()
            if DEBUG
            else structlog.processors.JSONRenderer(),
        },
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json_formatter",
        },
    },
    "loggers": {
        # Root logger configuration
        "": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": True,
        },
        # Django framework logs
        "django": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False,
        },
        # Application-specific logs with debug level
        "api": {
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Structlog processor configuration
# Configures the structured logging pipeline for consistent log formatting
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

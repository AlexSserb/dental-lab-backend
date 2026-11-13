import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Access environment variables
load_dotenv()
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_HOST = os.getenv("DATABASE_HOST")

SECRET_KEY = os.getenv("SECRET_KEY")

AI_BASE_URL = os.getenv("AI_BASE_URL") or None  # None -> https://api.openai.com/v1
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "")
AI_TIMEOUT_S = float(os.getenv("AI_TIMEOUT_S") or 60)
AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES") or 2)
# Max work types shown to the model per draft request (the catalog is narrowed down when larger)
AI_MAX_CANDIDATES = int(os.getenv("AI_MAX_CANDIDATES") or 20)
# Context window of the model in tokens; a warning is logged when a prompt uses >80% of it (0 = off)
AI_CONTEXT_TOKENS = int(os.getenv("AI_CONTEXT_TOKENS") or 0)
# USD per 1M tokens, used for cost estimates (0 for local models)
AI_PRICE_INPUT_PER_1M = os.getenv("AI_PRICE_INPUT_PER_1M") or "0"
AI_PRICE_OUTPUT_PER_1M = os.getenv("AI_PRICE_OUTPUT_PER_1M") or "0"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "bge-m3")
# Knowledge base (RAG): fragments passed to the LLM and the cosine-distance cutoff above which a fragment is
# considered unrelated (calibrate with `manage.py eval_retrieval`, see README).
KNOWLEDGE_TOP_K = int(os.getenv("KNOWLEDGE_TOP_K") or 4)
KNOWLEDGE_MAX_DISTANCE = float(os.getenv("KNOWLEDGE_MAX_DISTANCE") or 0.55)
# Reranking: a cross-encoder re-scores the hybrid-search candidates and keeps the best KNOWLEDGE_TOP_K.
# The model runs inside the backend process (CPU, ONNX) and is downloaded once into RERANK_CACHE_DIR.
RERANK_ENABLED = (os.getenv("RERANK_ENABLED") or "true").lower() in ("1", "true", "yes")
RERANK_MODEL = os.getenv("RERANK_MODEL") or "BAAI/bge-reranker-v2-m3-int8"
RERANK_CANDIDATES = int(os.getenv("RERANK_CANDIDATES") or 20)
# With reranking on, a fragment is kept only if its cross-encoder score (a raw logit: roughly > 0 relevant,
# about -11 for off-topic text) is at least this; it replaces the vector-distance cutoff. Calibrate with eval_retrieval.
KNOWLEDGE_MIN_RERANK_SCORE = float(os.getenv("KNOWLEDGE_MIN_RERANK_SCORE") or -5.0)
RERANK_CACHE_DIR = os.getenv("RERANK_CACHE_DIR") or os.path.join(BASE_DIR, ".cache", "fastembed")


def env_list(name: str, default: str = "") -> list[str]:
    """Reads a comma-separated environment variable as a list of non-empty strings."""
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

DEBUG = os.getenv("DEBUG", "False").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # External Packages
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "pgtrigger",
    "pghistory",
    # Internal Apps
    "core",
    "accounts",
    "orders",
    "works",
    "operations",
    "llm",
    "knowledge",
    "defects",
]

AUTH_USER_MODEL = "accounts.User"

# Application definition


SITE_ID = 1

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
    "djangorestframework_camel_case.middleware.CamelCaseMiddleWare",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "app.wsgi.application"

# Database

ACCOUNT_EMAIL_VERIFICATION = "none"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "PORT": DATABASE_PORT,
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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

LOGIN_ATTEMPT_LIMIT = 5  # max wrong passwords
LOGIN_LOCKOUT_SECONDS = 5 * 60  # how long the user is locked (5 min)

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

USE_TZ = True

LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "UTC"

USE_I18N = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [
    Path(BASE_DIR) / Path("static/"),
]

MEDIA_ROOT = Path(BASE_DIR) / Path("media")

REST_AUTH_SERIALIZERS = {"USER_DETAILS_SERIALIZER": "api.serializers.UserSerializer"}

# react dev local (5173) and react prod (80) by default
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "http://localhost:5173,http://localhost")

CSRF_COOKIE_NAME = "csrftoken"

# This will avoid the need for an SMTP server as e-mails will be printed to the console.
# For more information, please refer to:
# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# SMTP SETTINGS
EMAIL_HOST = "smtp.yandex.ru"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_ADMIN = EMAIL_HOST_USER
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
CLIENT_URL = os.getenv("CLIENT_URL")

# REST_AUTH_SERIALIZERS = {'LOGIN_SERIALIZER': 'api.serializers.LoginSerializer'}
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
        "djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseFormParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "COERCE_DECIMAL_TO_STRING": False,
    "DEFAULT_THROTTLE_RATES": {
        "order_draft": os.getenv("AI_DRAFT_RATE", "20/hour"),
        "knowledge_ask": os.getenv("KNOWLEDGE_ASK_RATE", "60/hour"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "JTI_CLAIM": "jti",
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "DentalLab project API",
    "VERSION": "1.0.0",
    # Split components into request and response parts where appropriate
    "COMPONENT_SPLIT_REQUEST": False,
    # Aid client generator targets that have trouble with read-only properties.
    "COMPONENT_NO_READ_ONLY_REQUIRED": False,
    # Create separate components for PATCH endpoints (without required list)
    "COMPONENT_SPLIT_PATCH": True,
    "SCHEMA_PATH_PREFIX": "/api",
    "SCHEMA_PATH_PREFIX_TRIM": True,
    "SERVE_INCLUDE_SCHEMA": False,
    "CAMELIZE_NAMES": True,
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.contrib.djangorestframework_camel_case.camelize_serializer_fields",
    ],
    "PARSER_WHITELIST": ["rest_framework.parsers.JSONParser"],
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

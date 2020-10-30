"""
Django settings for hyperlog project.

Generated by 'django-admin startproject' using Django 2.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
from datetime import timedelta

import environ

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()
env.read_env(os.path.join(BASE_DIR, ".env"))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env(
    "SECRET_KEY", default="_+58xeow@)vj%9!f48h^z)hd_(c3q(nljh4x3(o5l@q5c491yx"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = (
    ["staging.gateway.hyperlog.io", "gateway.hyperlog.io", "localhost"]
    if DEBUG is False
    else ["*"]
)


# Application definition

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # third-party apps
    "channels",
    "corsheaders",
    "graphene_django",
    # local apps
    "apps.base",
    "apps.users",
    "apps.profiles",
    "apps.widgets",
]

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
]

CORS_ORIGIN_WHITELIST = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://127.0.0.1:3000",
    "https://127.0.0.1:3000",
    "http://app.hyperlog.io",
    "https://app.hyperlog.io",
]

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = "hyperlog.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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


# Channels

ASGI_APPLICATION = "hyperlog.routing.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": env("POSTGRES_NAME", default="hyperlog"),
        "USER": env("POSTGRES_USER", default="postgres"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="postgres"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default=5432),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",  # noqa: E501
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/static/"

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")


# GitHub OAuth

GITHUB_CLIENT_ID = env("GITHUB_CLIENT_ID", default="")
GITHUB_CLIENT_SECRET = env("GITHUB_CLIENT_SECRET", default="")
GITHUB_REDIRECT_URI = env("GITHUB_REDIRECT_URI", default="")


# GitHub Auth (auth app) OAuth

GITHUB_AUTH_CLIENT_ID = env("GITHUB_AUTH_CLIENT_ID", default="")
GITHUB_AUTH_CLIENT_SECRET = env("GITHUB_AUTH_CLIENT_SECRET", default="")


# StackOverflow OAuth / API (Stack Exchange)

STACK_OVERFLOW_CLIENT_ID = env("STACK_OVERFLOW_CLIENT_ID", default="")
STACK_OVERFLOW_CLIENT_SECRET = env("STACK_OVERFLOW_CLIENT_SECRET", default="")
STACK_OVERFLOW_REDIRECT_URI = env("STACK_OVERFLOW_REDIRECT_URI", default="")
STACK_OVERFLOW_KEY = env("STACK_OVERFLOW_KEY", default="")


# GRAPHQL

GRAPHENE = {
    "SCHEMA": "hyperlog.schema.schema",
    "MIDDLEWARE": [
        "graphql_jwt.middleware.JSONWebTokenMiddleware",
        "apps.base.middleware.JWTVerifyNewestTokenMiddleware",
    ],
}


# DJANGO

AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = [
    "graphql_jwt.backends.JSONWebTokenBackend",
    "django.contrib.auth.backends.ModelBackend",
]
EMAIL_BACKEND = "django_ses.SESBackend"


# Whitenoise

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


# AWS

AWS_ACCOUNT_ID = str(env("AWS_ACCOUNT_ID", default="x"))  # Ensure str type
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="x")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="x")
AWS_DEFAULT_REGION = env("AWS_DEFAULT_REGION", default="us-east-1")

AWS_DDB_PROFILES_TABLE = env("AWS_DDB_PROFILES_TABLE", default="profiles")
AWS_DDB_PROFILE_ANALYSIS_TABLE = (
    env("AWS_DDB_PROFILE_ANALYSIS_TABLE", default="profile-analysis")
    + f"-{'prod' if DEBUG is False else 'dev'}"
)

AWS_SES_REGION_ENDPOINT = f"email.{AWS_DEFAULT_REGION}.amazonaws.com"
AWS_SES_RESET_PASSWORD_EMAIL = "Hyperlog Support <support@hyperlog.io>"
AWS_SES_REPLYTO_EMAIL = "Aditya from Hyperlog <aditya@hyperlog.io>"

AWS_SNS_PROFILE_ANALYSIS_TOPIC = (
    env("AWS_SNS_PROFILE_ANALYSIS_TOPIC", default="RepoAnalysis")
    + f"-{'prod' if DEBUG is False else 'dev'}"
)
AWS_SNS_USER_DELETE_TOPIC = (
    env("AWS_SNS_USER_DELETE_TOPIC", default="user_delete")
    + f"-{'prod' if DEBUG is False else 'dev'}"
)


# Sentry

sentry_sdk.init(
    "https://70c4499546b84ccdb5954017d91bde23@o310860.ingest.sentry.io/1777522"
    if DEBUG is False
    else None,
    integrations=[DjangoIntegration()],
)


# GRAPHQL_JWT (django-graphql-jwt app)

GRAPHQL_JWT = {
    "JWT_VERIFY_EXPIRATION": True,
    "JWT_EXPIRATION_DELTA": timedelta(days=15),
    "JWT_DECODE_HANDLER": "apps.base.jwt_conf.jwt_decode_handler",
    "JWT_PAYLOAD_HANDLER": "apps.base.jwt_conf.jwt_payload_handler",
    "JWT_PAYLOAD_GET_USERNAME_HANDLER": "apps.base.jwt_conf.jwt_payload_get_username_handler",  # noqa: E501
    "JWT_GET_USER_BY_NATURAL_KEY_HANDLER": "apps.base.jwt_conf.jwt_payload_get_user_by_natural_key_handler",  # noqa: E501
}


# JWT

JWT_CUSTOM_COOKIE_MIDDLEWARE_MAX_AGE = 30  # seconds


# Telegram

TG_BOT_SOURCE = env("TG_BOT_SOURCE")
TG_TOKEN_HASH = env("TG_TOKEN_HASH")

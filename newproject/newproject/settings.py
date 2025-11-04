from pathlib import Path
import os
import ssl
import certifi
from django.conf.global_settings import EMAIL_USE_TLS
import dj_database_url  # ✅ for PostgreSQL connection

ssl._create_default_https_context = lambda: ssl._create_unverified_context()

BASE_DIR = Path(__file__).resolve().parent.parent

EMAIL_BACKEND = 'projectapp.email_backend.CustomEmailBackend'

SECRET_KEY = 'django-insecure-your-secret-key'
DEBUG = True
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'projectapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'newproject.urls'

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

WSGI_APPLICATION = 'newproject.wsgi.application'

# ✅ DATABASE (Render PostgreSQL)
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,  # keeps connection alive
        ssl_require=True   # required for Render
    )
}

# Password validation
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

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# ✅ Razorpay Keys
RAZORPAY_KEY_ID = "rzp_test_RaUbYZKXoHR2IT"
RAZORPAY_KEY_SECRET = "s7EwhvUXxwl9ieMzM69r7d4W"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ✅ EMAIL CONFIGURATION (TLS Mode — Works with Gmail)
import smtplib
ssl._create_default_https_context = ssl._create_unverified_context

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'bhaskaryhubale.899@gmail.com'
EMAIL_HOST_PASSWORD = 'your_16_digit_app_password'  # App password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
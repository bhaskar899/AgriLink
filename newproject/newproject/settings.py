from pathlib import Path
import os
import ssl
import dj_database_url

# ---------------------
# BASE DIRECTORY
# ---------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------
# SECURITY
# ---------------------
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-your-secret-key')
DEBUG = True  # Render par error dekhne ke liye True rakhein, baad mein False kar dena
ALLOWED_HOSTS = ['*']

# ---------------------
# APPLICATIONS
# ---------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'projectapp',
    'cloudinary_storage',
    'cloudinary',
    'channels',
    'rest_framework',
    'api',
]

ASGI_APPLICATION = 'newproject.asgi.application'

# ---------------------
# CHANNEL LAYERS (REDIS FIX FOR RENDER)
# ---------------------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {
            # Render par 127.0.0.1 nahi chalta. REDIS_URL environment variable use karein.
            "hosts": [os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379')],
        },
    }
}

# ---------------------
# MIDDLEWARE
# ---------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ---------------------
# URLS & WSGI
# ---------------------
ROOT_URLCONF = 'newproject.urls'
WSGI_APPLICATION = 'newproject.wsgi.application'

# ---------------------
# TEMPLATES
# ---------------------
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
                'projectapp.context_processors.navbar_notifications',
            ],
        },
    },
]

# ---------------------
# DATABASE
# ---------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ---------------------
# PASSWORD VALIDATION
# ---------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------
# LOCALIZATION
# ---------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True
USE_L10N = True

# ---------------------
# STATIC & MEDIA FILES
# ---------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------
# CLOUDINARY SETTINGS
# ---------------------
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dhjactcwx',
    'API_KEY': '543344718597668',
    'API_SECRET': '5hrZqEM1zB3qTfZa8oNzvSCDzF8',
}

# ---------------------
# RAZORPAY
# ---------------------
RAZORPAY_KEY_ID = "rzp_live_SHWiIZFCskqFhT"
RAZORPAY_KEY_SECRET = "QD36AGTlyzRhuwdLVziqWNUj"

# ---------------------
# EMAIL CONFIGURATION (FIXED FOR DEPLOYMENT)
# ---------------------
# CustomBackend agar crash ho raha hai toh default use karna behtar hai
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# Render Environment Variables se uthayega, warna default use karega
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'bhaskaryhubale.899@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'liox giwz dlvz mpov')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ---------------------
# AUTHENTICATION REDIRECTS
# ---------------------
LOGIN_URL = 'retailer_login'
LOGIN_REDIRECT_URL = 'retailer_dashboard'
LOGOUT_REDIRECT_URL = 'home'

# ---------------------
# DEFAULT FIELD TYPE & MISC
# ---------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
PLATFORM_COMMISSION = 0.05

# IMPORTANT: Render/Production mein ye SSL bypass avoid karein
if not os.environ.get('RENDER'):
    ssl._create_default_https_context = lambda: ssl._create_unverified_context()
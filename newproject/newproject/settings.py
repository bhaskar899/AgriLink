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
SECRET_KEY = 'django-insecure-your-secret-key'
DEBUG = False  # Deploy ke liye False
ALLOWED_HOSTS = ['*']  # Change to your domain for production

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
    'projectapp',
    'cloudinary_storage',
    'cloudinary',
    'channels',
]

ASGI_APPLICATION = 'newproject.asgi.application'

# ---------------------
# CHANNELS
# ---------------------
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],  # Replace with Render Redis host in prod
        },
    }
}

# ---------------------
# MIDDLEWARE
# ---------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # for static files
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
if os.environ.get('RENDER'):
    DATABASES = {
        'default': dj_database_url.config(
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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------------
# STATIC & MEDIA
# ---------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------
# MEDIA (CLOUDINARY)
# ---------------------
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = None  # Cloudinary handles uploads

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dhjactcwx',
    'API_KEY': '543344718597668',
    'API_SECRET': '5hrZqEM1zB3qTfZa8oNzvSCDzF8',
}

# ---------------------
# RAZORPAY
# ---------------------
RAZORPAY_KEY_ID = "rzp_test_RaUbYZKXoHR2IT"
RAZORPAY_KEY_SECRET = "s7EwhvUXxwl9ieMzM69r7d4W"

# ---------------------
# EMAIL CONFIGURATION
# ---------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'bhaskaryhubale.899@gmail.com'
EMAIL_HOST_PASSWORD = 'app-password-from-gmail'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ---------------------
# DEFAULT FIELD TYPE
# ---------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------
# SSL FIX (Local Only)
# ---------------------
ssl._create_default_https_context = lambda: ssl._create_unverified_context()

PLATFORM_COMMISSION = 0.05

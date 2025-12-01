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
# 🔥 Render Environment से SECRET_KEY लें
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-your-secret-key-fallback')

# 🔥 Render पर DEBUG = False सेट करें, लोकल टेस्टिंग के लिए True रखें
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# 🔥 Render पर ALLOWED_HOSTS को 'ALLOWED_HOSTS' variable से लें
# इसे Render पर अपने डोमेन (agrilink-7899.onrender.com) से भरें
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

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
    'channels'
]

# ---------------------
# ASGI & CHANNELS
# ---------------------
ASGI_APPLICATION = 'newproject.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        # CRITICAL FIX: Render पर Redis का URL Environment Variable से लें
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {
            # सुनिश्चित करें कि आपने Render पर REDIS_URL environment variable सेट किया है
            "hosts": [os.environ.get('REDIS_URL', "redis://127.0.0.1:6379")],
        },
    }
}

# ---------------------
# MIDDLEWARE
# ---------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise को हमेशा SecurityMiddleware के ठीक बाद रखें
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
# Render पर DATABASE_URL environment variable का उपयोग करें
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR}/db.sqlite3'),
        conn_max_age=600,
        ssl_require=True
    )
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
# STATIC & MEDIA FILES
# ---------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
# MEDIA_ROOT अब Cloudinary में चला जाएगा

# ---------------------
# CLOUDINARY SETTINGS (MEDIA/IMAGE FIX)
# ---------------------
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

CLOUDINARY_STORAGE = {
    # 🔥 FIX: Render पर CLOUDINARY_CLOUD_NAME Environment Variable सेट करें
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    # 🔥 FIX: Render पर CLOUDINARY_API_KEY Environment Variable सेट करें
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    # 🔥 FIX: Render पर CLOUDINARY_API_SECRET Environment Variable सेट करें
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

# ---------------------
# RAZORPAY (Environment Variables से लें)
# ---------------------
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

# ---------------------
# EMAIL CONFIGURATION (OTP FIX)
# ---------------------
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'

# 🔥 FIX: Render पर EMAIL_HOST_USER और PASSWORD सेट करें
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
# ---------------------

# ---------------------
# DEFAULT FIELD TYPE
# ---------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------
# SSL FIX (Local Only)
# ---------------------
# इसे सिर्फ लोकल (local) डेवलपमेंट के लिए रखें
if DEBUG:
    ssl._create_default_https_context = lambda: ssl._create_unverified_context()

PLATFORM_COMMISSION = 0.05
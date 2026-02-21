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
DEBUG = False  # change to False when done testing
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

# settings.py

# ... (other settings) ...

CHANNEL_LAYERS = {
    "default": {
        # ⚠️ CRITICAL FIX: Use Redis for inter-process communication
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {
            # Change this to your actual Redis location/credentials if needed
            "hosts": [("127.0.0.1", 6379)],
        },
    }
}

# ... (rest of the settings) ...

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
                'projectapp.context_processors.navbar_notifications',  # <- Add this
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
# EMAIL CONFIGURATION
# ---------------------
# 📧 EMAIL SETTINGS
# IMPORTANT — Use custom backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# ↑ project folder name EXACT same jisme settings.py hai

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'bhaskaryhubale.899@gmail.com'
EMAIL_HOST_PASSWORD = 'liox giwz dlvz mpov'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# ---------------------
# DEFAULT FIELD TYPE
# ---------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------
# SSL FIX (Local Only)
# ---------------------
ssl._create_default_https_context = lambda: ssl._create_unverified_context()

PLATFORM_COMMISSION = 0.05   # 5% default

# settings.py

# settings.py

# 1. Time zone enable karein
USE_TZ = True

# 2. Apne time zone ko set karein
# India Standard Time (IST) ke liye
TIME_ZONE = 'Asia/Kolkata'

# 3. Agar aap dates ko local time mein dikhana chahte hain:
USE_L10N = True

# ---------------------
# AUTHENTICATION REDIRECTS
# ---------------------
LOGIN_URL = 'retailer_login'  # Agar login nahi hai toh yahan bhejega
LOGIN_REDIRECT_URL = 'retailer_dashboard'  # Login hone ke baad yahan bhejega
LOGOUT_REDIRECT_URL = 'home'  # Logout hone ke baad yahan bhejega
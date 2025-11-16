from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'dev-secret'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
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

ROOT_URLCONF = 'dealer_project.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ]
    }
}]

WSGI_APPLICATION = 'dealer_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dealer_db',
        'USER': 'postgres',
        'PASSWORD': 'root',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

AUTH_USER_MODEL = 'core.AdminUser'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# API Authentication settings
API_AUTHENTICATION_ENABLED = True

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365 * 100),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# ============================================================================
# Email Configuration
# ============================================================================

# For Development: Use console backend (prints emails to terminal)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# For Production: Use SMTP backend (uncomment and configure below)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'  # Gmail SMTP server
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = 'your-email@gmail.com'  # Replace with your email
# EMAIL_HOST_PASSWORD = 'your-app-password'  # Replace with your Gmail app password
# DEFAULT_FROM_EMAIL = 'your-email@gmail.com'  # Replace with your email

# For Gmail App Password:
# 1. Go to https://myaccount.google.com/apppasswords
# 2. Enable 2-factor authentication if not enabled
# 3. Generate an app password
# 4. Use that password in EMAIL_HOST_PASSWORD

# For other email providers (e.g., Outlook, Yahoo, custom SMTP):
# Outlook:
# EMAIL_HOST = 'smtp-mail.outlook.com'
# EMAIL_PORT = 587

# Yahoo:
# EMAIL_HOST = 'smtp.mail.yahoo.com'
# EMAIL_PORT = 587

# Custom SMTP:
# EMAIL_HOST = 'smtp.yourdomain.com'
# EMAIL_PORT = 587  # or 465 for SSL
# EMAIL_USE_TLS = True  # or EMAIL_USE_SSL = True for port 465
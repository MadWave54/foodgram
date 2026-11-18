import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'foodgram-local-development-key')
DEBUG = os.getenv('DEBUG', '0') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,backend').split(',')
CSRF_TRUSTED_ORIGINS = os.getenv(
    'CSRF_TRUSTED_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080'
).split(',')
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth',
    'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.messages', 'django.contrib.staticfiles',
    'rest_framework', 'rest_framework.authtoken', 'djoser',
    'users', 'recipes',
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
ROOT_URLCONF = 'foodgram.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]
WSGI_APPLICATION = 'foodgram.wsgi.application'
if os.getenv('POSTGRES_DB'):
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['POSTGRES_DB'],
        'USER': os.environ['POSTGRES_USER'],
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST': os.getenv('DB_HOST', 'db'), 'PORT': '5432',
    }}
else:
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }}
AUTH_USER_MODEL = 'users.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'api.pagination.FoodgramPagination',
    'PAGE_SIZE': 6,
}
DJOSER = {
    'LOGIN_FIELD': 'email',
    'USER_CREATE_PASSWORD_RETYPE': False,
    'HIDE_USERS': False,
    'SERIALIZERS': {
        'user_create': 'api.serializers.RegisterSerializer',
        'user': 'api.serializers.UserSerializer',
        'current_user': 'api.serializers.UserSerializer',
    },
    'PERMISSIONS': {
        'user_list': ['rest_framework.permissions.AllowAny'],
        'user': ['rest_framework.permissions.AllowAny'],
    },
}

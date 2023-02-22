"""
Django settings for repository_similarity project.

Generated by 'django-admin startproject' using Django 4.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-9cd+5@f7gxnv5&b7(^s&n_3@n-@+u%r5^sy@7q4_x0t+72x#&%"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "Users",
    "corsheaders",
    #"storages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = ['https://web-production-8d3b.up.railway.app']
CSRF_TRUSTED_ORIGINS = ['https://*.web-production-8d3b.up.railway.app']

WHITENOISE_ALLOW_ALL_ORIGINS = True

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True


ROOT_URLCONF = "repository_similarity.urls"

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

WSGI_APPLICATION = "repository_similarity.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.mysql",
#         "NAME": "railway",
#         "USER": "root",
#         "PASSWORD": "UrmxvNgDlAwIGunVHQeq",
#         "HOST": "containers-us-west-184.railway.app",
#         "PORT": "5858",
#         "OPTIONS": {
#             "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
#             "charset": "utf8mb4",
#         },
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQLDATABASE'),
        'USER': os.environ.get('MYSQLUSER'),
        'PASSWORD': os.environ.get('MYSQLPASSWORD'),
        'HOST': os.environ.get('MYSQLHOST'),
        'PORT': os.environ.get('MYSQLPORT'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media/")
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [os.path.join(BASE_DIR, "Users/static")]

STORAGES = {
    # ...
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

#AMAZON S3

# AWS_ACCESS_KEY_ID = 'YOUR_ACCESS_KEY'
# AWS_SECRET_ACCESS_KEY = 'YOUR_SECRET_KEY'
# AWS_STORAGE_BUCKET_NAME = 'YOUR_BUCKET_NAME'

# AWS_S3_FILE_OVERWRITE = False
# AWS_DEFAULT_ACL = None
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# AWS_S3_REGION_NAME = 'YOUR_REGION_NAME' 
# AWS_S3_ENDPOINT_URL = 'YOUR_ENDPOINT_URL'

# MEDIA_ROOT = '/media/'
# MEDIA_URL = 'https://s3-us-west-2.amazonaws.com/YOUR_BUCKET_NAME/'


# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "Users.User"

#Emailing settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_FROM = 'tubat.mark09@gmail.com'
EMAIL_HOST_USER = 'tubat.mark09@gmail.com'
EMAIL_HOST_PASSWORD = 'wqwhxbrsrmzmwyxn'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Railway.app-specific email settings
if 'RAILWAY_APP_NAME' in os.environ:
    EMAIL_HOST = os.environ.get('SMTP_HOST')
    EMAIL_PORT = int(os.environ.get('SMTP_PORT', 587))
    EMAIL_HOST_USER = os.environ.get('SMTP_USERNAME')
    EMAIL_HOST_PASSWORD = os.environ.get('SMTP_PASSWORD')
    EMAIL_USE_TLS = bool(os.environ.get('SMTP_TLS', True))
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'tubat.mark09@gmail.com')


PASSWORD_RESET_TIMEOUT = 14400 #available token for 4 hours
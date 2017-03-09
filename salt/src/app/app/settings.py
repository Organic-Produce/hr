"""
Django settings for app project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

import re

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'rpc0*u2&b7)==0ar8#q(jqob9vhh!7u#rj2rv9e#fza_(#f8r='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

DEFAULT_FROM_EMAIL = 'ramon@hrpower.com'

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend' #'django.core.mail.backends.smtp.EmailBackend'

EMAIL_FILE_PATH = '/tmp/clock-messages'

IGNORABLE_404_URLS = (
    re.compile(r'^/apple-touch-icon.*\.png$'),
        re.compile(r'^/favicon\.ico$'),
            re.compile(r'^/robots\.txt$'),
            )

ALLOWED_HOSTS = [
    '.hrpower.com', # Allow domain and subdomains
    '.hrpower.com.', # Also allow FQDN and subdomains
    '*'
        ]


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    # third-party
    'compressor',
    'floppyforms',
    'gmapi',
    'haystack',
    'south',
    'rest_framework',
    'rest_framework.authtoken',
    'djcelery',
    'BruteBuster',
    'select_multiple_field',  
    'registration', 

    # first-party
    'profiles', 
    'clock',
    'dataprep',   
    'register', 
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware', 
    'django.middleware.csrf.CsrfViewMiddleware',
    'BruteBuster.middleware.RequestMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)

ROOT_URLCONF = 'app.urls'

WSGI_APPLICATION = 'app.wsgi.application'

BROKER_URL = 'amqp://clock:clock@localhost:5672//'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'clock',
        'USER': 'clock_data',
        'PASSWORD': 'clock',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'search',
    }
}

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
HAYSTACK_SEARCH_RESULTS_PER_PAGE=3

REST_FRAMEWORK = {
    #'DEFAULT_MODEL_SERIALIZER_CLASS': 'rest_framework.serializers.HyperlinkedModelSerializer',
    #'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',]
    'DEFAULT_AUTHENTICATION_CLASSES' : ('rest_framework.authentication.TokenAuthentication',)
}

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
)

ELASTICSEARCH_HOST = 'localhost'

ACCOUNT_ACTIVATION_DAYS = 7

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

from django.utils.translation import ugettext_lazy as _
LANGUAGES = (
    ('en', _('English')),
    ('es', _('Spanish')),
)

LOCALE_PATHS = ( os.path.join(BASE_DIR, 'locale'), )

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/static/files/'


STATIC_ROOT = os.path.join(BASE_DIR, "static/")
MEDIA_ROOT = os.path.join(BASE_DIR, "static/files/")

#### Others

AUTH_USER_MODEL = 'profiles.Profile'

TEMPLATE_DIRS = (
    '%s/templates/' % BASE_DIR,
)

# compressor
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (
    ('text/scss', 'sass --scss {infile} {outfile}'),
)

COMPRESS_ROOT = '%s/static/' % BASE_DIR


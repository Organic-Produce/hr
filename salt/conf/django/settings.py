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
DEBUG = {% if grains['id'] == 'clock-internals.local' %}True{% else %}False{% endif %}

TEMPLATE_DEBUG = True

ADMINS = (('Ramon', 'ramon@hrpower.com'),)

MANAGERS =  (('Ramon', 'ramon@hrpower.com'),)

DEFAULT_FROM_EMAIL = 'ramon@hrpower.com'

#EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend' #'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_FILE_PATH = '/tmp/clock-messages'

EMAIL_HOST = 'mail.hrpower.com'
EMAIL_HOST_USER = 'ramon@hrpower.com'
EMAIL_HOST_PASSWORD = '123456'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

SERVER_EMAIL = 'ramon@hrpower.com'

EMAIL_SUBJECT_PREFIX = '[HR Power] '

IGNORABLE_404_URLS = (
    re.compile(r'^/apple-touch-icon.*\.png$'),
        re.compile(r'^/favicon\.ico$'),
            re.compile(r'^/robots\.txt$'),
            )

ALLOWED_HOSTS = [
    '.hrpower.com', # Allow domain and subdomains
    '.hrpower.com.', # Also allow FQDN and subdomains
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
    'select_multiple_field', {% if grains['id'] == 'clock-internals.locall' %}
    'debug_toolbar', {% endif %} {% if grains['id'] == 'clock-internals.local' %}
    'registration', {% endif %}

    # first-party
    'profiles', 
    'clock',{% if 'squirtle' or 'local' in grains['id'] %}
    'dataprep', {% endif %} {% if 'cucaracha' in grains['id'] %}
    'tax', {% endif %} {% if grains['id'] == 'clock-internals.local' %}
    'register', {% endif %}
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware', {% if grains['id'] == 'clock-internals.locall' %}
    'debug_toolbar.middleware.DebugToolbarMiddleware',{% endif %}
    'django.middleware.csrf.CsrfViewMiddleware',
    'BruteBuster.middleware.RequestMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)

ROOT_URLCONF = 'app.urls'

WSGI_APPLICATION = 'app.wsgi.application'

BROKER_URL = 'amqp://{{ pillar['rabbit']['user'] }}:{{ pillar['rabbit']['password'] }}@{{ pillar['rabbit']['host'] }}:{{ pillar['rabbit']['port'] }}//'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': '{{ pillar['database']['engine'] }}',
        'NAME': '{{ pillar['database']['name'] }}',
        'USER': '{{ pillar['database']['user'] }}',
        'PASSWORD': '{{ pillar['database']['password'] }}',
        'HOST': '{{ pillar['database']['host'] }}',
        'PORT': '{{ pillar['database']['port'] }}',
    }
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': '{{ pillar['elasticsearch']['engine'] }}',
        'URL': '{{ pillar['elasticsearch']['url'] }}',
        'INDEX_NAME': 'search',
    }
}

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
{% if grains['id'] == 'clock-internals.local' %}HAYSTACK_SEARCH_RESULTS_PER_PAGE=3{% endif %}
{% if grains['id'] == 'clock-internals.locall' %}
DEBUG_TOOLBAR_PATCH_SETTINGS = False
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TEMPLATE_CONTEXT': True,
} 
INTERNAL_IPS = ('127.0.0.1','172.31.44.223','54.68.173.71')
DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS': False,}
def show_toolbar(request):
    return True
SHOW_TOOLBAR_CALLBACK = show_toolbar
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'haystack_panel.panel.HaystackDebugPanel',
]
{% endif %}
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

ELASTICSEARCH_HOST = '{{ pillar['elasticsearch']['host'] }}'

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



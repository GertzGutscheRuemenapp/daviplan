from tempfile import mkdtemp
from datentool.settings_dev import *


MEDIA_ROOT = mkdtemp(prefix='media_')

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'circle_test',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}


OSRM_ROUTING = {
    'CAR': {
        'alias': 'car',
        'host': 'localhost',
        'service_port': 8001,
        'routing_port': 5001,
    },
    'BIKE': {
        'alias': 'bicycle',
        'host': 'localhost',
        'service_port': 8001,
        'routing_port': 5002,
    },
    'WALK': {
        'alias': 'foot',
        'host': 'localhost',
        'service_port': 8001,
        'routing_port': 5003,
    },
}

# workaround: deactivate loggers may cause errors while running tests in circleci
# LOGGING['loggers'] = {}
# sync=True preserves database connections, disabled for circleci

USE_DJANGO_Q = False

LOCALE = 'en_US'
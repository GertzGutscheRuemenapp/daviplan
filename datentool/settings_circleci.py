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
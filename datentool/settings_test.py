from datentool.settings_dev import *


DATABASES['default'] = {
    'spatialite': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': ':memory:',
    },
    }

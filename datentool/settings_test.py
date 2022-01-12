from datentool.settings_dev import *

DATABASES['default'] = {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': ':memory:',
    }

from datentool.settings_local import *

from tempfile import mkdtemp

MEDIA_ROOT = mkdtemp(prefix='media_')
USE_DJANGO_Q = False

LOGGING['handlers']['debug_console'] = {'level': 'DEBUG',
                                        'class': 'logging.StreamHandler'}


LOGGING['loggers']['test']={
            'handlers': ['debug_console'],
            'level': 'DEBUG',
            'propagate': False,
        }

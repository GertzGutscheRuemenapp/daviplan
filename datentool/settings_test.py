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

OSRM_ROUTING = {
    'CAR': {
        'alias': 'car',
        'host': os.environ.get('MODE_CAR_HOST', 'localhost'),
        'service_port': os.environ.get('MODE_CAR_SERVICE_PORT', 8011),
        'routing_port': os.environ.get('MODE_CAR_ROUTING_PORT', 5011),
    },
    'BIKE': {
        'alias': 'bicycle',
        'host': os.environ.get('MODE_BIKE_HOST', 'localhost'),
        'service_port': os.environ.get('MODE_BIKE_SERVICE_PORT', 8011),
        'routing_port': os.environ.get('MODE_BIKE_ROUTING_PORT', 5012),
    },
    'WALK': {
        'alias': 'foot',
        'host': os.environ.get('MODE_WALK_HOST', 'localhost'),
        'service_port': os.environ.get('MODE_WALK_SERVICE_PORT', 8011),
        'routing_port': os.environ.get('MODE_WALK_ROUTING_PORT', 5013),
    },
}


STEPSIZE = 20

ROUTING_ALGORITHM = 'ch'

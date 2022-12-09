from datentool.settings_local import *

from tempfile import mkdtemp

MEDIA_ROOT = mkdtemp(prefix='media_')
USE_DJANGO_Q = False

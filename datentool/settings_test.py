from datentool.settings_local import *

from tempfile import mkdtemp

MEDIA_ROOT = mkdtemp(prefix='media_')
Q_CLUSTER['sync'] = True

from datentool.settings import *

#INSTALLED_APPS.extend([
    #'corsheaders'
#])

#MIDDLEWARE.extend([
    #'corsheaders.middleware.CorsMiddleware',
    #'django.middleware.common.CommonMiddleware'
#])

#CORS_ORIGIN_ALLOW_ALL = True

DEBUG = True

# GDAL
if os.name == 'nt':
    # alternate install via conda
    os.environ['GDAL_DATA'] = os.path.join(sys.prefix, 'Library',
                                           'share', 'gdal')
    os.environ['PATH'] = ';'.join([os.environ['PATH'],
                                   os.path.join(sys.prefix, 'Library', 'bin')])

DATABASES['default']['OPTIONS']['sslmode'] = 'prefer'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-mzejv_pa9tbj7$5$q%ju0ko*)vrouq3_+0&q)y@phi!fevpntp'

ALLOWED_HOSTS.extend([
    'localhost',
    '127.0.0.1'
])
from datentool.settings import *

DEBUG = True

INSTALLED_APPS.extend([
    'corsheaders'
])

# cors midleware has to be loaded first
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware'
] + MIDDLEWARE

CORS_ORIGIN_ALLOW_ALL = True

# allow access to Rest API with session in development only
# (in production only auth. via tokens is allowed)
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].extend([
    'rest_framework.authentication.SessionAuthentication',
])

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
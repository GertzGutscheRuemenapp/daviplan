from datentool.settings import *

DEBUG = True

INSTALLED_APPS.extend([
    'corsheaders'
])

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
ALLOWED_HOSTS = ['*']

LOGGING['handlers']['web_socket']['level'] = 'DEBUG'

# cors midleware has to be loaded first
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware'
] + MIDDLEWARE

# allow access to Rest API with session in development only
# (in production only auth. via tokens is allowed)
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].extend([
    'rest_framework.authentication.SessionAuthentication',
])

DATABASES['default']['OPTIONS']['sslmode'] = 'prefer'

# default secret keys, for dev only!
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-mzejv_pa9tbj7$5$q%ju0ko*)vrouq3_+0&q)y@phi!fevpntp'
)
# dummy encryption key - don't use this one in production
ENCRYPT_KEY = os.environ.get('ENCRYPT_KEY',
                             '85Ao9Yoarq05G2p_QsD_zDg5FTdOc3OaA2SndOBP55s=')

# set to False to run django_q tasks synchronous in dev mode without
# needing running seperate q-cluster
USE_DJANGO_Q = True

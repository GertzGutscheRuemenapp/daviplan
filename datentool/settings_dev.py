from datentool.settings import *

DEBUG = True

INSTALLED_APPS.extend([
    'corsheaders'
])

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
ALLOWED_HOSTS = ['*']
#ALLOWED_HOSTS.extend([
    #'localhost',
    #'127.0.0.1',
    #'0.0.0.0'
#])

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

# set to True to run  django_q tasks synchronous in dev mode without
# needing running seperate q-cluster
Q_CLUSTER['sync'] = False

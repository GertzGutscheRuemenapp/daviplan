from datentool.settings import *

DEBUG = True

LOGGING['handlers']['web_socket']['level'] = 'DEBUG'
LOGGING['handlers']['console']['level'] = 'DEBUG'

# allow access to Rest API with session in development only
# (in production only auth. via tokens is allowed)
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].extend([
    'rest_framework.authentication.SessionAuthentication',
])

DATABASES['default']['OPTIONS']['sslmode'] = 'prefer'

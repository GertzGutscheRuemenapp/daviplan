"""
WSGI config for datentool project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

import locale

# set locale to german style
locale.setlocale(locale.LC_ALL, 'de_DE')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'datentool.settings')

application = get_wsgi_application()

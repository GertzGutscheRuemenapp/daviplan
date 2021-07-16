### GDAL
two options under Windows
- with OSGeo4W Installer (settings.py):
https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/#windows
- with conda installation (settings_dev.py):
conda install -c conda-forge gdal=3.1 (global)

### Rest API is protected
- in development (settings_dev.py) access with an active session is allowed
(log in via /django-admin/login)
- in production only tokens are allowed (receive via /api/token)
- verification of token in header: {"Authorization": "Bearer *received token*"}

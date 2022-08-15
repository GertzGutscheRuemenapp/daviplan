### GDAL
two options under Windows
- with OSGeo4W Installer (settings.py):
https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/#windows
- with conda installation (settings_dev.py):
conda install -c conda-forge gdal=3.1 (global)
# install osmium-tool and protobuf (needed for vector-tiles)
conda install -c conda-forge osmium-tool protobuf

### Rest API is protected
- in development (settings_dev.py) access with an active session is allowed
(log in via /django-admin/login)
- in production only tokens are allowed (receive via /api/token)
- verification of token in header: {"Authorization": "Bearer *received token*"}

### Serve Frontend
\<path to installation\>/angular-frontend/npm install
\<path to installation\>/angular-frontend/ng build --stats-json
 - argument --stats-json creates stats file that provides information to django about the built hashed resources
 - add argument --watch to reload on change

### export fixtures for area (very slow when creating it with hypothesis)
dumpdata datentool_backend.mapsymbols datentool_backend.layergroup datentool_backend.internalwfslayer datentool_backend.source datentool_backend.arealevel datentool_backend.area --indent 2 >test.json

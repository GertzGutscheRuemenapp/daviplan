### GDAL
two options under Windows
- with OSGeo4W Installer (settings.py):
# Bule Datentool

a web tool to display and plan basic public services

## Setting up a development environment

https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/#windows
with conda installation (settings_dev.py):
- conda install -c conda-forge gdal=3.4 shapely osmium-tool protobuf pip pyproj (global)
install osmium-tool and protobuf (needed for vector-tiles)
conda install -c conda-forge osmium-tool protobuf

### Rest API is protected
- in development (settings_dev.py) access with an active session is allowed
(log in via /django-admin/login)
- in production only tokens are allowed (receive via /api/token)
- verification of token in header: {"Authorization": "Bearer *received token*"}

### Serve Frontend
Install the dependencies:
- \<path to installation\>/angular-frontend/npm install --force
There are two options to serve the Javascript-files:
- use an IDE to run the frontend
- to serve them solely with django you have to bundle them first:
\<path to installation\>/angular-frontend/ng build --stats-json
  > add argument --watch to reload on change

## Productive Server
see /dist/README.md


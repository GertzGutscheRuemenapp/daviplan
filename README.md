# Bule Datentool

a web tool to display and plan basic public services

## Setting up a development environment

### GDAL
two options to install GDAL under Windows
- with OSGeo4W Installer (settings.py):
  > https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/#windows
- with conda installation (settings_dev.py):
  > conda install -c conda-forge gdal=3.4 shapely osmium-tool protobuf pip pyproj (global)

### Osmium Tools (needed for vector-tiles)
install osmium-tool and protobuf
<em>conda install -c conda-forge osmium-tool protobuf</em>

### Python dependencies
preferably in a separated environment run:
<em>pip install -r requirements.txt</em>

### Database
- set up a PostGIS database
- create a custom settings file importing from settings_dev.py (or settings_dev_alt_gdal.py)
- override the database defaults (name, user, port etc.) in the your settings file to match your local database
- migrate database
  > <em>python manage.py migrate settings=datentool.yoursettingsfile</em>
- create superuser
  > <em>python manage.py createsuperuser settings=datentool.yoursettingsfile</em>
- initialize database
  > <em>python manage.py initproject settings=datentool.yoursettingsfile</em>

### Other services needed
- Redis required for logging and django_q
  > run as docker-container e.g. <em>redis:7.0.4</em>
- OSRM containers required for routing
  > run as docker-container <em>gertzgutscheruemenapp/osrm-flask</em>

### Serve Frontend
Install the dependencies:
- <em>\<path to installation\>/angular-frontend/npm install --force</em>
There are two options to serve the Javascript-files:
- use an IDE to run the frontend
- serve them solely with django. in that case you have to bundle them manually:
<em>\<path to installation\>/angular-frontend/ng build --stats-json</em>
  > add argument <em>--watch</em> to reload on change

### Serve backend
- run the cluster, required for pushing background tasks (if <em>Q_CLUSTER['sync'] = False</em> in settings)
  > <em>python manage.py qcluster settings=datentool.yoursettingsfile</em>
- run the backend
  > <em>python manage.py runserver 8000 settings=datentool.yoursettingsfile</em>
  > you may swap the port with any other port you like. the site will be available there (if you serve the frontend with django)

### Rest API is protected
- in development (settings_dev.py) access with an active session is allowed
(log in via <em>/django-admin/login</em>)
- in production only tokens are allowed (receive via <em>/api/token</em>)
- verification of token in header: {"Authorization": "Bearer *received token*"}

## Productive Server
see /dist/README.md


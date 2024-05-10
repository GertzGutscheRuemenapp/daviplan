# daviplan

Webtool zur Planung und Darstellung von Strukturen der regionalen Daseinsvorsorge

A web tool to display and plan basic public services

Homepage: [daviplan.de](https://daviplan.de/installation)

## Software Manuals / Handbücher

Auf der Homepage finden Sie die Handbücher zur [Installation](https://daviplan.de/installation) und [Anwendung der Software](https://daviplan.de/nutzung) als PDFs.

At the homepage you can find the PDF [installation](https://daviplan.de/installation) and [operating](https://daviplan.de/nutzung) manuals in german.

## Status

Testing Status

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/GertzGutscheRuemenapp/bule_datentool/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/gh/GertzGutscheRuemenapp/bule_datentool/tree/main)

Code Coverage

[![codecov](https://codecov.io/gh/GertzGutscheRuemenapp/bule_datentool/branch/main/graph/badge.svg?token=18FTTI6MF5)](https://codecov.io/gh/GertzGutscheRuemenapp/bule_datentool)

## Version
see /datentool_backend/version.py

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
  > add argument <em>--configuration development</em> if you are in a development environment
  > add argument <em>--watch</em> to reload on change

### Serve backend
- run the cluster, required for pushing background tasks (if <em>Q_CLUSTER['sync'] = False</em> in settings)
  > <em>python manage.py qcluster settings=datentool.yoursettingsfile</em>
- run the backend
  > <em>python manage.py runserver 8000 settings=datentool.yoursettingsfile</em>.
  > you may swap the port with any other port you like. The site will be available there (in case you serve the frontend with django)

### Rest API is protected
- in development (settings_dev.py) access with an active session is allowed
(log in via <em>/django-admin/login</em>)
- in production only tokens are allowed (receive via <em>/api/token</em>)
- verification of token in header: {"Authorization": "Bearer *received token*"}

## Productive Server
see /dist/README.md


#!/bin/bash
echo "Initializing daviplan"
if [[ $ENVIRONMENT == "DEV" ]];
then
	export DJANGO_SETTINGS_MODULE=datentool.settings_dev	
fi
cd /datentool/
python /datentool/manage.py migrate --run-syncdb 
python /datentool/manage.py qcluster &

if [[ $ENVIRONMENT == "DEV" ]];
then 
	echo "Preparing resources for local test mode"
	cd /datentool/angular-frontend 
	npm i
	ng build --stats-json --configuration development 
	cd /datentool/
	echo "Starting in local test mode (localhost only!)"
	python manage.py runserver 0.0.0.0:8000
else 
	echo "Preparing resources for productive mode"
	python manage.py collectstatic --no-input 
	echo "Starting in productive mode"
	daphne -b 0.0.0.0 -p 8000 datentool.asgi:application
fi
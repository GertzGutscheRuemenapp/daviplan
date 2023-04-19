#!/bin/bash
echo "Initializing daviplan"
if [[ $ENVIRONMENT == "development" ]]; 
then
	export DJANGO_SETTINGS_MODULE=datentool.settings_dev	
elif [[ $ENVIRONMENT == "staging" ]]; then
	export DJANGO_SETTINGS_MODULE=datentool.settings_staging	
fi
cd /datentool/
python /datentool/manage.py migrate --run-syncdb 
python /datentool/manage.py qcluster &

if [[ $ENVIRONMENT == "development" || $ENVIRONMENT == "staging" ]]; then 
	echo "Preparing resources for $ENVIRONMENT mode"
	cd /datentool/angular-frontend 
	npm i
	ng build --stats-json --configuration $ENVIRONMENT 
	cd /datentool/
	echo "Starting in $ENVIRONMENT mode"
	python manage.py runserver 0.0.0.0:8000
else 
	echo "Preparing resources for productive mode"
	python manage.py collectstatic --no-input 
	echo "Starting in productive mode"
	daphne -b 0.0.0.0 -p 8000 datentool.asgi:application
fi
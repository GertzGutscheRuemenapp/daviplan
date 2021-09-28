CALL conda activate datentool
CALL coverage run --source='.' manage.py test datentool_backend --settings=datentool.settings_test
CALL coverate html
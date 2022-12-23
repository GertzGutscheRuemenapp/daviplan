CALL conda activate datentool
CALL cd %~dp0
CALL coverage run --source='.' manage.py test datentool_backend --settings=datentool.settings_test
CALL coverage html

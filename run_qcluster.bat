CALL conda activate datentool
CALL cd %~dp0
CALL python manage.py qcluster --settings=datentool.settings_local

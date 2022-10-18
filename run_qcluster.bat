CALL conda activate datentool2
CALL cd %~dp0
CALL python manage.py qcluster --settings=datentool.settings_local

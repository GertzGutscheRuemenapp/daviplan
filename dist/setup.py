import secrets
from collections import OrderedDict
from cryptography.fernet import Fernet

outputs = OrderedDict({
    'DJANGO_SETTINGS_MODULE': ('datentool.settings', 'settings file, either datentool.settings for productive use or datentool.settings_dev in development'),
    'ENCRYPT_KEY': ('', 'URL-safe base64-encoded 32-byte key used for en/decrypting of BKG Geocode and Regionalstatistik API passwords'),
    'ALLOWED_HOSTS': ('*', 'URLs or IPs of hosts, that are allowed to do certain queries on the server (comma-seperated without https://, should at least include the domain this site is on'),
    'SECRET_KEY':  ('', 'Secret key django is using to secure signed data  '),
    'EXT_PORT':  ('8090', 'port the site and the API will be locally available at (localhost:{EXT_PORT}'),
    'DB_HOST': ('postgis', 'host of the database (defaults to "postgis" as linked in docker-compose)'),
    'DB_NAME': ('datentool', 'name of the database (defaults to datentool), created on docker-compose start up'),
    'DB_USER': ('postgres', 'database user (defaults to the default postgis-container user "postgres")'),
    'DB_PASS': ('', 'password of the database user (defaults to None, default database is not protected)'),
    'DB_PORT': ('5432', 'port of the database (defaults to 5432)')
})

print()
title = 'Konfiguration des Datentools und Erzeugung der Umgebungsvariablen.'
print('-' * len(title))
print(title)
print('-' * len(title))
print()

print('Schlüssel um abgezeichnete Daten (Sessions etc.) zu schützen')
print('Frei lassen, um einen Schlüssel generieren zu lassen.')
secret_key = input('Schlüssel eingeben: ')
if not secret_key:
    secret_key = secrets.token_urlsafe(32)
outputs['SECRET_KEY'] = (secret_key, outputs['SECRET_KEY'][1])
print(secret_key)
print()

print('Schlüssel zur Verschlüsselung der Passwörter der BKG- und Regionalstatistik-Konten in der Datenbank.')
print('Achtung: eine Änderung des Schlüssels führt zur Invalidierung bereits gespeicherter Passwörter dieser Konten.')
print('Frei lassen, um einen Schlüssel generieren zu lassen.')
fernet_key = input('Schlüssel (URL-safe base64-encoded 32-byte) eingeben: ')
if not fernet_key:
    fernet_key = Fernet.generate_key().decode('utf-8')
outputs['ENCRYPT_KEY'] = (fernet_key, outputs['ENCRYPT_KEY'][1])
print(fernet_key)
print()

print('Name der Domain, über die die Seite des Datentools erreichbar sein wird.')
print('z.B datentool.domain.de oder datentool-regional.de')
while True:
    domain = input('Name der Domain (ohne https://): ')
    if domain:
        outputs['ALLOWED_HOSTS'] = (domain, outputs['ALLOWED_HOSTS'][1])
        break
print(domain)
print()

with open('.env', 'w') as file:
    for env_var, (value, description) in outputs.items():
        if description:
            file.write('# ' + description + '\n')
        file.write(env_var + '=' + value + '\n\n')

print('Einstellungen in Datei .env geschrieben.')

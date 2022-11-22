from cryptography.fernet import Fernet, InvalidToken
import base64
from django.conf import settings

def encrypt(pas):
    pas = str(pas)
    cipher_pass = Fernet(settings.ENCRYPT_KEY)
    encrypt_pass = cipher_pass.encrypt(pas.encode('ascii'))
    encrypt_pass = base64.urlsafe_b64encode(encrypt_pass).decode("ascii")
    return encrypt_pass

def decrypt(pas):
    pas = base64.urlsafe_b64decode(pas)
    cipher_pass = Fernet(settings.ENCRYPT_KEY)
    try:
        decod_pass = cipher_pass.decrypt(pas).decode("ascii")
    except InvalidToken:
        raise Exception('Der für die Passwortverschlüsselung benutzte Key '
                        'ist nicht gültig. Wenden Sie sich bitte an Ihren '
                        'Administrator')
    return decod_pass
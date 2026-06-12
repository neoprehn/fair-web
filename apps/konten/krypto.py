"""Verschlüsselung für sensible Nutzer-Daten (z. B. KI-API-Keys).

Leitet einen Fernet-Schlüssel aus ``settings.SECRET_KEY`` ab. Damit ist
kein separates Secret-Management nötig – der Schlüssel ändert sich mit
``SECRET_KEY`` (z. B. bei einem Secret-Rotation müssten gespeicherte
Werte neu erfasst werden, was für API-Keys unkritisch ist).
"""

import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet():
    schluessel = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(schluessel))


def verschluesseln(klartext: str) -> str:
    if not klartext:
        return ""
    return _fernet().encrypt(klartext.encode("utf-8")).decode("ascii")


def entschluesseln(token: str) -> str:
    if not token:
        return ""
    return _fernet().decrypt(token.encode("ascii")).decode("utf-8")

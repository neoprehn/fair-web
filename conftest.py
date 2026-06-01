"""Pytest-Bootstrap.

Wird von pytest VOR dem Laden der Django-Settings importiert. Wir setzen
hier Test-Umgebungsvariablen. ``django-environ.read_env`` überschreibt
bereits gesetzte ``os.environ``-Werte nicht – dadurch laufen Tests gegen
eine flüchtige SQLite-DB, während die echte ``.env`` (MariaDB) unberührt
bleibt.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-nicht-fuer-produktion")
os.environ.setdefault("DEBUG", "False")

import pytest


@pytest.fixture
def client(client, django_user_model):
    """Eingeloggter Test-Client – die App hat App-weite Login-Pflicht und
    rollenbasierte Rechte. Der Standard-Client ist Superuser (umgeht
    Permission-Checks); Rollen-Tests erzeugen sich eigene Nutzer/Clients.
    """
    user = django_user_model.objects.create_superuser(
        username="testadmin", password="pw-test-12345", email="t@t.de"
    )
    client.force_login(user)
    return client

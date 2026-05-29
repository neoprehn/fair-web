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

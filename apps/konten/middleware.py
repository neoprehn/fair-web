"""Login-Pflicht für die gesamte App.

Nicht angemeldete Nutzer werden auf die Login-Seite umgeleitet – ausgenommen
sind Login/Logout/Registrierung (``/accounts/``), der Django-Admin (eigener
Login) sowie statische Dateien und Medien.
"""

from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect

EXEMPT_PREFIXES = ("/accounts/", "/admin/", "/static/", "/media/")


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info
            if not any(path.startswith(p) for p in EXEMPT_PREFIXES):
                ziel = f"{settings.LOGIN_URL}?{urlencode({'next': request.get_full_path()})}"
                return redirect(ziel)
        return self.get_response(request)

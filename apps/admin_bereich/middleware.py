"""Aktiviert das Zahlenformat-Locale passend zur globalen Währung.

EUR → Locale ``de`` (1.234,56), USD → Locale ``en`` (1,234.56). Damit folgen
sowohl die Ausgabe (``intcomma``/``floatformat``) als auch das Parsen der
lokalisierten Formularfelder der eingestellten Währung.
"""

from django.utils import translation


class WaehrungLocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            from .models import AppKonfiguration
            translation.activate(AppKonfiguration.load().locale_code)
        except Exception:  # noqa: BLE001 – z. B. vor der ersten Migration
            pass
        try:
            return self.get_response(request)
        finally:
            # Auf den Standard (LANGUAGE_CODE) zurück – kein Locale-Leak zwischen Requests.
            translation.deactivate()

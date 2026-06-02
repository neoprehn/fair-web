"""Tests für die (immer aktiven) Sicherheits-Header."""

from django.test import Client
from django.urls import reverse


def test_sicherheits_header_aktiv():
    resp = Client().get(reverse("login"))
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("Referrer-Policy") == "same-origin"
    assert resp.headers.get("X-Frame-Options") == "DENY"


def test_wsgi_erzwingt_https_nur_wenn_aktiv(settings):
    from config.wsgi import _force_https_wrapper

    def stub(environ, start_response):
        return []

    # SECURE_HTTPS aus -> Schema unverändert.
    settings.SECURE_HTTPS = False
    env = {"wsgi.url_scheme": "http"}
    _force_https_wrapper(stub)(env, lambda *a: None)
    assert env["wsgi.url_scheme"] == "http"

    # SECURE_HTTPS an -> Schema + Header auf https erzwungen.
    settings.SECURE_HTTPS = True
    env = {"wsgi.url_scheme": "http"}
    _force_https_wrapper(stub)(env, lambda *a: None)
    assert env["wsgi.url_scheme"] == "https"
    assert env["HTTP_X_FORWARDED_PROTO"] == "https"

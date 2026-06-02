"""Tests für die (immer aktiven) Sicherheits-Header."""

from django.test import Client
from django.urls import reverse


def test_sicherheits_header_aktiv():
    resp = Client().get(reverse("login"))
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("Referrer-Policy") == "same-origin"
    assert resp.headers.get("X-Frame-Options") == "DENY"

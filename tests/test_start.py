"""Tests für die Startseite (Phase 9: Home/Modell-Erklärung)."""

import pytest
from django.test import Client
from django.urls import reverse


def test_start_url_ist_root():
    assert reverse("start") == "/"


def test_start_anonym_login_pflicht():
    resp = Client().get(reverse("start"))
    assert resp.status_code == 302
    assert reverse("login") in resp.url


@pytest.mark.django_db
def test_start_zeigt_fair_baum(client):
    html = client.get(reverse("start")).content.decode()
    assert "FAIR" in html
    assert 'class="svg-node startnode"' in html
    assert 'id="knoten-infos"' in html  # Erklärungen fürs Klick-Panel


@pytest.mark.django_db
def test_szenarien_dashboard_unter_szenarien_prefix(client):
    assert reverse("szenarien:dashboard") == "/szenarien/"
    assert client.get(reverse("szenarien:dashboard")).status_code == 200

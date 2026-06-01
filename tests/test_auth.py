"""Tests für die App-weite Login-Pflicht (Phase 7, Slice 1)."""

import pytest
from django.test import Client
from django.urls import reverse


def test_anonym_wird_zum_login_umgeleitet():
    c = Client()  # bewusst nicht eingeloggt
    resp = c.get(reverse("szenarien:dashboard"))
    assert resp.status_code == 302
    assert reverse("login") in resp.url
    assert "next=" in resp.url


def test_login_seite_ist_ohne_anmeldung_erreichbar():
    c = Client()
    assert c.get(reverse("login")).status_code == 200


@pytest.mark.django_db
def test_eingeloggt_erreicht_dashboard(client):
    # 'client' ist via conftest bereits eingeloggt.
    assert client.get(reverse("szenarien:dashboard")).status_code == 200


@pytest.mark.django_db
def test_login_und_logout(django_user_model):
    django_user_model.objects.create_user(username="alice", password="pw-test-12345")
    c = Client()
    ok = c.login(username="alice", password="pw-test-12345")
    assert ok
    assert c.get(reverse("szenarien:dashboard")).status_code == 200
    # Logout ist POST-only (Django 5).
    resp = c.post(reverse("logout"))
    assert resp.status_code == 302
    # Danach wieder Login-Pflicht.
    assert c.get(reverse("szenarien:dashboard")).status_code == 302

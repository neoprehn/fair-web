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


def test_registrierung_ohne_login_erreichbar():
    c = Client()
    assert c.get(reverse("konten:registrieren")).status_code == 200


@pytest.mark.django_db
def test_registrierung_legt_inaktiven_betrachter_an(django_user_model):
    c = Client()
    resp = c.post(reverse("konten:registrieren"), {
        "username": "neuling",
        "password1": "ein-gutes-pw-123",
        "password2": "ein-gutes-pw-123",
    })
    assert resp.status_code == 302 and resp.url == reverse("login")
    user = django_user_model.objects.get(username="neuling")
    assert user.groups.filter(name="Betrachter").exists()
    assert user.is_active is False
    # Konto ist inaktiv -> Login schlägt fehl, Dashboard nicht erreichbar.
    login_resp = c.post(reverse("login"), {
        "username": "neuling",
        "password": "ein-gutes-pw-123",
    })
    assert login_resp.status_code == 200  # Formular mit Fehler, kein Redirect
    assert c.get(reverse("szenarien:dashboard")).status_code == 302


@pytest.mark.django_db
def test_brute_force_schutz_sperrt_nach_zu_vielen_fehlversuchen(django_user_model):
    django_user_model.objects.create_user(username="bob", password="pw-test-12345")
    c = Client()
    for _ in range(5):
        resp = c.post(reverse("login"), {
            "username": "bob", "password": "falsches-pw",
        })
        assert resp.status_code in (200, 429)
    # Nach AXES_FAILURE_LIMIT=5 ist auch der korrekte Login gesperrt.
    resp = c.post(reverse("login"), {
        "username": "bob", "password": "pw-test-12345",
    })
    assert resp.status_code == 429


@pytest.mark.django_db
def test_login_und_logout(django_user_model):
    django_user_model.objects.create_user(username="alice", password="pw-test-12345")
    c = Client()
    resp = c.post(reverse("login"), {
        "username": "alice", "password": "pw-test-12345",
    })
    assert resp.status_code == 302
    assert c.get(reverse("szenarien:dashboard")).status_code == 200
    # Logout ist POST-only (Django 5).
    resp = c.post(reverse("logout"))
    assert resp.status_code == 302
    # Danach wieder Login-Pflicht.
    assert c.get(reverse("szenarien:dashboard")).status_code == 302

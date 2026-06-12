"""Tests für die pro-Nutzer-KI-Einstellungen (Provider/Modell/API-Key)."""

import pytest
from django.urls import reverse

from apps.konten import krypto
from apps.konten.models import KIEinstellung


def test_krypto_roundtrip():
    klartext = "sk-test-12345"
    token = krypto.verschluesseln(klartext)
    assert token != klartext
    assert krypto.entschluesseln(token) == klartext


def test_krypto_leerer_text():
    assert krypto.verschluesseln("") == ""
    assert krypto.entschluesseln("") == ""


@pytest.mark.django_db
def test_set_api_key_verschluesselt_und_liest_zurueck(django_user_model):
    user = django_user_model.objects.create_user(username="bob", password="pw-test-12345")
    einstellung = KIEinstellung(user=user)
    einstellung.set_api_key("sk-geheim")
    einstellung.save()
    geladen = KIEinstellung.objects.get(user=user)
    assert geladen.api_key_verschluesselt != "sk-geheim"
    assert geladen.api_key == "sk-geheim"
    assert geladen.hat_api_key is True


@pytest.mark.django_db
def test_ist_konfiguriert():
    einstellung = KIEinstellung()
    assert einstellung.ist_konfiguriert is False
    einstellung.provider = KIEinstellung.Provider.ANTHROPIC
    einstellung.modell = "claude-sonnet-4-6"
    einstellung.set_api_key("sk-geheim")
    assert einstellung.ist_konfiguriert is True


def test_ki_einstellungen_erfordert_login():
    from django.test import Client
    c = Client()
    resp = c.get(reverse("konten:ki_einstellungen"))
    assert resp.status_code == 302
    assert reverse("login") in resp.url


@pytest.mark.django_db
def test_ki_einstellungen_get_und_post(client):
    # 'client' ist via conftest eingeloggter Superuser.
    resp = client.get(reverse("konten:ki_einstellungen"))
    assert resp.status_code == 200

    resp = client.post(reverse("konten:ki_einstellungen"), {
        "provider": "anthropic",
        "modell": "claude-sonnet-4-6",
        "api_key": "sk-geheim",
    })
    assert resp.status_code == 302

    einstellung = KIEinstellung.objects.get(user__username="testadmin")
    assert einstellung.provider == "anthropic"
    assert einstellung.modell == "claude-sonnet-4-6"
    assert einstellung.api_key == "sk-geheim"


@pytest.mark.django_db
def test_ki_einstellungen_leerer_api_key_behaelt_bestehenden(client):
    client.post(reverse("konten:ki_einstellungen"), {
        "provider": "anthropic",
        "modell": "claude-sonnet-4-6",
        "api_key": "sk-erster-key",
    })
    # Zweites Speichern ohne neuen Key -> bestehender bleibt erhalten.
    resp = client.post(reverse("konten:ki_einstellungen"), {
        "provider": "openai",
        "modell": "gpt-4o",
        "api_key": "",
    })
    assert resp.status_code == 302
    einstellung = KIEinstellung.objects.get(user__username="testadmin")
    assert einstellung.provider == "openai"
    assert einstellung.modell == "gpt-4o"
    assert einstellung.api_key == "sk-erster-key"

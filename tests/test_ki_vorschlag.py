"""Tests für den KI-Assistenten-Endpunkt (ki_vorschlag) und ki_service."""

import pytest
from django.urls import reverse

from apps.konten.models import KIEinstellung
from apps.szenarien import ki_service


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


@pytest.mark.django_db
def test_frage_ki_ohne_konfiguration_wirft_kifehler(django_user_model):
    user = django_user_model.objects.create_user(username="ohne-ki", password="pw-test-12345")
    with pytest.raises(ki_service.KIFehler):
        ki_service.frage_ki(user, "system", "frage")


@pytest.mark.django_db
def test_frage_ki_ruft_litellm_mit_provider_modell(django_user_model, monkeypatch):
    user = django_user_model.objects.create_user(username="mit-ki", password="pw-test-12345")
    einstellung = KIEinstellung(user=user, provider="anthropic", modell="claude-sonnet-4-6")
    einstellung.set_api_key("sk-test")
    einstellung.save()

    aufrufe = {}

    def fake_completion(**kwargs):
        aufrufe.update(kwargs)
        return _FakeResponse("  Vorschlagstext  ")

    monkeypatch.setattr(ki_service.litellm, "completion", fake_completion)

    antwort = ki_service.frage_ki(user, "system-prompt", "Bitte formulieren.")
    assert antwort == "Vorschlagstext"
    assert aufrufe["model"] == "anthropic/claude-sonnet-4-6"
    assert aufrufe["api_key"] == "sk-test"
    assert aufrufe["messages"][0] == {"role": "system", "content": "system-prompt"}


@pytest.mark.django_db
def test_frage_ki_fehler_wird_zu_kifehler(django_user_model, monkeypatch):
    user = django_user_model.objects.create_user(username="mit-ki-fehler", password="pw-test-12345")
    einstellung = KIEinstellung(user=user, provider="openai", modell="gpt-4o")
    einstellung.set_api_key("sk-test")
    einstellung.save()

    def fake_completion(**kwargs):
        raise RuntimeError("ungültiger Key")

    monkeypatch.setattr(ki_service.litellm, "completion", fake_completion)

    with pytest.raises(ki_service.KIFehler):
        ki_service.frage_ki(user, "system-prompt", "Frage")


@pytest.mark.django_db
def test_ki_vorschlag_ohne_berechtigung(django_user_model):
    from django.test import Client
    user = django_user_model.objects.create_user(username="betrachter", password="pw-test-12345")
    c = Client()
    c.force_login(user)
    resp = c.post(reverse("szenarien:ki_vorschlag"), {"feld": "beschreibung", "name": "Test"})
    assert resp.status_code == 403


@pytest.mark.django_db
def test_ki_vorschlag_ohne_konfiguration(client):
    resp = client.post(reverse("szenarien:ki_vorschlag"), {
        "feld": "beschreibung", "name": "Mein Szenario",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is False
    assert "KI-Einstellungen" in data["fehler"]


@pytest.mark.django_db
def test_ki_vorschlag_beschreibung_mit_konfiguration(client, django_user_model, monkeypatch):
    user = django_user_model.objects.get(username="testadmin")
    einstellung = KIEinstellung(user=user, provider="anthropic", modell="claude-sonnet-4-6")
    einstellung.set_api_key("sk-test")
    einstellung.save()

    monkeypatch.setattr(ki_service.litellm, "completion",
                        lambda **kw: _FakeResponse("Neue Beschreibung"))

    resp = client.post(reverse("szenarien:ki_vorschlag"), {
        "feld": "beschreibung", "name": "Mein Szenario", "frage": "Bitte formulieren",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"ok": True, "antwort": "Neue Beschreibung"}


@pytest.mark.django_db
def test_ki_vorschlag_annahmen_mit_konfiguration(client, django_user_model, monkeypatch):
    user = django_user_model.objects.get(username="testadmin")
    einstellung = KIEinstellung(user=user, provider="anthropic", modell="claude-sonnet-4-6")
    einstellung.set_api_key("sk-test")
    einstellung.save()

    monkeypatch.setattr(ki_service.litellm, "completion",
                        lambda **kw: _FakeResponse("Begründung für TC"))

    resp = client.post(reverse("szenarien:ki_vorschlag"), {
        "feld": "TC-annahmen",
        "code": "TC",
        "name": "Mein Szenario",
        "beschreibung": "Phishing-Angriff auf Mitarbeitende",
        "TC-verteilung": "pert",
        "TC-unsicherheit": "2",
        "TC-low": "1",
        "TC-mode": "3",
        "TC-high": "5",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"ok": True, "antwort": "Begründung für TC"}


@pytest.mark.django_db
def test_ki_vorschlag_unbekanntes_feld(client, django_user_model):
    user = django_user_model.objects.get(username="testadmin")
    einstellung = KIEinstellung(user=user, provider="anthropic", modell="claude-sonnet-4-6")
    einstellung.set_api_key("sk-test")
    einstellung.save()

    resp = client.post(reverse("szenarien:ki_vorschlag"), {
        "feld": "XYZ-annahmen", "code": "XYZ", "name": "Test",
    })
    assert resp.status_code == 200
    assert resp.json() == {"ok": False, "fehler": "Unbekanntes Feld."}

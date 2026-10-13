"""Tests für den CAM-KI-Assistenten-Endpunkt (cam_ki_vorschlag).

Nutzt denselben generischen ki_service wie apps.szenarien - siehe dortiges
tests/test_ki_vorschlag.py für die ki_service-eigenen Tests. Hier nur der
CAM-spezifische Teil: Prompt-Aufbau + Endpunkt-Verdrahtung.
"""

import pytest

pytest.importorskip("litellm", exc_type=ImportError)

from django.urls import reverse

from apps.cam.beispiele import RANSOMWARE_BEISPIEL
from apps.cam.models import CamSzenario
from apps.konten.models import KIEinstellung

from test_cam_views import _post_ransomware


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


def _mit_ki_konfiguriert(django_user_model, client):
    user = django_user_model.objects.create_user(username="mit-ki", password="pw-test-12345")
    einstellung = KIEinstellung(user=user, provider="anthropic", modell="claude-sonnet-4-6")
    einstellung.set_api_key("sk-test")
    einstellung.save()
    client.force_login(user)
    return user


@pytest.mark.django_db
def test_cam_ki_vorschlag_ohne_berechtigung_403(client, django_user_model):
    user = django_user_model.objects.create_user(username="ohne-recht", password="pw-test-12345")
    client.force_login(user)
    resp = client.post(reverse("cam:ki_vorschlag"), data={"code": "early"})
    assert resp.status_code == 403


@pytest.mark.django_db
def test_cam_ki_vorschlag_ohne_ki_konfiguration(client, django_user_model):
    from django.contrib.auth.models import Permission

    user = django_user_model.objects.create_user(username="kein-ki", password="pw-test-12345")
    user.user_permissions.add(Permission.objects.get(codename="add_camszenario"))
    client.force_login(user)
    resp = client.post(reverse("cam:ki_vorschlag"), data={"code": "early"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is False
    assert "KI-Einstellungen" in resp.json()["fehler"]


@pytest.mark.django_db
def test_cam_ki_vorschlag_baut_prompt_und_gibt_antwort_zurueck(client, django_user_model, monkeypatch):
    from django.contrib.auth.models import Permission

    user = _mit_ki_konfiguriert(django_user_model, client)
    user.user_permissions.add(Permission.objects.get(codename="add_camszenario"))

    aufrufe = {}

    def fake_completion(**kwargs):
        aufrufe.update(kwargs)
        return _FakeResponse("Branchenwert laut Incident-Statistik 2026.")

    import litellm

    monkeypatch.setattr(litellm, "completion", fake_completion)

    b = RANSOMWARE_BEISPIEL
    data = {k: str(v) for k, v in b["szenario"].items()}
    data["early-klasse"] = "early"
    data["early-verteilung"] = "pert"
    data["early-low"] = "2000"
    data["early-mode"] = "8000"
    data["early-high"] = "30000"
    data["code"] = "early"
    data["frage"] = "Formuliere eine kurze Begründung."

    resp = client.post(reverse("cam:ki_vorschlag"), data=data)
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["antwort"] == "Branchenwert laut Incident-Statistik 2026."

    system_prompt = aufrufe["messages"][0]["content"]
    assert "Früh (early)" in system_prompt
    assert "CAM-Szenario" in system_prompt
    assert b["szenario"]["name"] in system_prompt
    assert "'low': 2000.0, 'mode': 8000.0, 'high': 30000.0" in system_prompt

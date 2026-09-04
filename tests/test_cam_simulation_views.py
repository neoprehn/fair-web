"""Tests für die CAM-Simulations-Views (Start, Status-Polling, Ergebnisseite)."""

import pytest
from django.urls import reverse

from apps.cam import views
from apps.cam.beispiele import RANSOMWARE_BEISPIEL
from apps.cam.models import CamControl, CamSimulationslauf, CamStage, CamSzenario, CamVerlustklasse


@pytest.fixture
def cam_szenario(db):
    b = RANSOMWARE_BEISPIEL
    daten = dict(b["szenario"])
    daten.update(n_simulations=500, random_seed=7)
    s = CamSzenario.objects.create(**daten)
    CamControl.objects.create(szenario=s, **b["control"])
    for stage in b["stages"]:
        CamStage.objects.create(szenario=s, **stage)
    for vk in b["verlustklassen"]:
        CamVerlustklasse.objects.create(szenario=s, **vk)
    return s


@pytest.mark.django_db
def test_starten_legt_lauf_an_und_leitet_weiter(client, cam_szenario, monkeypatch):
    # Hintergrund-Thread im Test NICHT wirklich starten.
    gestartet = {}
    monkeypatch.setattr(views, "starte_cam_simulation_async",
                        lambda lauf_id: gestartet.setdefault("id", lauf_id))

    resp = client.post(reverse("cam:starten", kwargs={"pk": cam_szenario.pk}))

    lauf = CamSimulationslauf.objects.get(szenario=cam_szenario)
    assert resp.status_code == 302
    assert resp.url == reverse("cam:lauf", kwargs={"pk": lauf.pk})
    assert lauf.n_simulations == 500 and lauf.random_seed == 7
    assert gestartet["id"] == lauf.pk  # Runner wurde angestoßen


@pytest.mark.django_db
def test_starten_nur_per_post(client, cam_szenario):
    resp = client.get(reverse("cam:starten", kwargs={"pk": cam_szenario.pk}))
    assert resp.status_code == 405  # GET nicht erlaubt


@pytest.mark.django_db
def test_status_endpunkt_liefert_json(client, cam_szenario):
    lauf = CamSimulationslauf.objects.create(
        szenario=cam_szenario, n_simulations=500, random_seed=7,
        status=CamSimulationslauf.Status.LAEUFT, fortschritt=42,
    )
    resp = client.get(reverse("cam:status", kwargs={"pk": lauf.pk}))
    assert resp.status_code == 200
    assert resp.json() == {"status": "laeuft", "fortschritt": 42}


@pytest.mark.django_db
def test_lauf_seite_zeigt_ergebnis(client, cam_szenario):
    lauf = CamSimulationslauf.objects.create(
        szenario=cam_szenario, n_simulations=500, random_seed=7,
        status=CamSimulationslauf.Status.FERTIG, fortschritt=100,
        ergebnis={"n": 500, "mittelwert": 12345.0, "median": 9000.0,
                  "min": 0.0, "max": 99999.0, "p90": 50000.0, "p95": 70000.0,
                  "p99": 90000.0, "perzentile": {}, "lec": [], "verteilung_hist": {},
                  "outcome_verteilung": {"klassen": ["early"], "anzahl": [500]},
                  "stage_erkennung": {"stufe": [1, 2, 3, 4, 5, 6],
                                       "anteil": [0.5, 0.1, 0.05, 0.02, 0.01, 0.01]},
                  "tef_mittel": 10.0, "susceptibility_mittel": 0.2, "lef_mittel": 2.0},
    )
    resp = client.get(reverse("cam:lauf", kwargs={"pk": lauf.pk}))
    assert resp.status_code == 200
    assert b"Erwarteter Jahresschaden" in resp.content
    # Kill-Chain-Diagramm zeigt die Stufennamen aus dem Ransomware-Beispiel.
    assert "Initial Access".encode() in resp.content
    assert "Lateral Movement".encode() in resp.content
    assert "Angreifer scheitert".encode() in resp.content


@pytest.mark.django_db
def test_detail_zeigt_berechnen_button(client, cam_szenario):
    resp = client.get(reverse("cam:detail", kwargs={"pk": cam_szenario.pk}))
    assert resp.status_code == 200
    assert b"Berechnen" in resp.content

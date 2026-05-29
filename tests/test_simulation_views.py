"""Tests für die Simulations-Views (Start, Status-Polling, Ergebnisseite)."""

import pytest
from django.urls import reverse

from apps.berechnung import views
from apps.berechnung.models import Simulationslauf
from apps.szenarien.models import FaktorEingabe, Szenario


@pytest.fixture
def szenario(db):
    s = Szenario.objects.create(name="Sim", n_simulations=500, random_seed=7)
    FaktorEingabe.objects.create(
        szenario=s, faktor="LEF", verteilung="pert",
        params={"low": 1, "mode": 3, "high": 6},
    )
    FaktorEingabe.objects.create(
        szenario=s, faktor="LM", verteilung="constant", params={"constant": 4000},
    )
    return s


@pytest.mark.django_db
def test_starten_legt_lauf_an_und_leitet_weiter(client, szenario, monkeypatch):
    # Hintergrund-Thread im Test NICHT wirklich starten.
    gestartet = {}
    monkeypatch.setattr(views, "starte_simulation_async",
                        lambda lauf_id: gestartet.setdefault("id", lauf_id))

    resp = client.post(reverse("berechnung:starten", kwargs={"szenario_pk": szenario.pk}))

    lauf = Simulationslauf.objects.get(szenario=szenario)
    assert resp.status_code == 302
    assert resp.url == reverse("berechnung:lauf", kwargs={"pk": lauf.pk})
    assert lauf.n_simulations == 500 and lauf.random_seed == 7
    assert gestartet["id"] == lauf.pk  # Runner wurde angestoßen


@pytest.mark.django_db
def test_starten_nur_per_post(client, szenario):
    resp = client.get(reverse("berechnung:starten", kwargs={"szenario_pk": szenario.pk}))
    assert resp.status_code == 405  # GET nicht erlaubt


@pytest.mark.django_db
def test_status_endpunkt_liefert_json(client, szenario):
    lauf = Simulationslauf.objects.create(
        szenario=szenario, n_simulations=500, random_seed=7,
        status=Simulationslauf.Status.LAEUFT, fortschritt=42,
    )
    resp = client.get(reverse("berechnung:status", kwargs={"pk": lauf.pk}))
    assert resp.status_code == 200
    assert resp.json() == {"status": "laeuft", "fortschritt": 42}


@pytest.mark.django_db
def test_lauf_seite_zeigt_ergebnis(client, szenario):
    lauf = Simulationslauf.objects.create(
        szenario=szenario, n_simulations=500, random_seed=7,
        status=Simulationslauf.Status.FERTIG, fortschritt=100,
        ergebnis={"n": 500, "mittelwert": 12345.0, "median": 9000.0,
                  "min": 0.0, "max": 99999.0, "p90": 50000.0, "p95": 70000.0,
                  "p99": 90000.0, "lec": []},
    )
    resp = client.get(reverse("berechnung:lauf", kwargs={"pk": lauf.pk}))
    assert resp.status_code == 200
    assert b"Erwarteter Jahresschaden" in resp.content


@pytest.mark.django_db
def test_detail_zeigt_berechnen_button(client, szenario):
    resp = client.get(reverse("szenarien:detail", kwargs={"pk": szenario.pk}))
    assert resp.status_code == 200
    assert b"Berechnen" in resp.content

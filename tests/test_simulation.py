"""Tests für die Monte-Carlo-Engine + Runner (Phase 4, Variante A)."""

import pytest

from apps.berechnung import services
from apps.berechnung.models import Simulationslauf
from apps.szenarien.models import FaktorEingabe, Szenario


def _szenario_mit_faktoren():
    s = Szenario.objects.create(name="Sim-Test", n_simulations=200)
    FaktorEingabe.objects.create(
        szenario=s, faktor="LEF", verteilung="pert",
        params={"low": 1, "mode": 3, "high": 6},
    )
    FaktorEingabe.objects.create(
        szenario=s, faktor="LM", verteilung="constant", params={"constant": 4000},
    )
    return s


@pytest.mark.django_db
def test_simuliere_liefert_kennzahlen_und_lec():
    pytest.importorskip("pyfair")
    s = _szenario_mit_faktoren()

    fortschritte = []
    ergebnis = services.simuliere(
        s, n_simulations=200, random_seed=42, batches=4,
        fortschritt=fortschritte.append,
    )

    assert ergebnis["n"] == 200
    for key in ("mittelwert", "median", "min", "max", "p90", "p95", "p99", "lec"):
        assert key in ergebnis
    assert ergebnis["min"] <= ergebnis["median"] <= ergebnis["max"]
    assert ergebnis["p90"] <= ergebnis["p99"]
    # LEC ist eine fallende Überschreitungskurve.
    assert len(ergebnis["lec"]) > 0
    assert ergebnis["lec"][0]["ueberschreitung"] >= ergebnis["lec"][-1]["ueberschreitung"]
    # Fortschritt endet bei 100.
    assert fortschritte[-1] == 100


@pytest.mark.django_db
def test_ergebnis_enthaelt_knoten_mit_status():
    pytest.importorskip("pyfair")
    s = _szenario_mit_faktoren()  # LEF (pert) + LM (constant) -> Eingaben
    ergebnis = services.simuliere(s, n_simulations=200, random_seed=42, batches=2)

    knoten = ergebnis["knoten"]
    assert knoten["LEF"]["status"] == "eingabe"
    assert knoten["LM"]["status"] == "eingabe"
    assert knoten["Risk"]["status"] == "berechnet"
    # Nicht genutzte Knoten (z. B. TEF) tauchen nicht auf.
    assert "TEF" not in knoten


@pytest.mark.django_db
def test_run_simulation_setzt_lauf_auf_fertig():
    pytest.importorskip("pyfair")
    s = _szenario_mit_faktoren()
    lauf = Simulationslauf.objects.create(szenario=s, n_simulations=200, random_seed=42)

    services._run_simulation(lauf.pk)  # synchron, ohne Thread

    lauf.refresh_from_db()
    assert lauf.status == Simulationslauf.Status.FERTIG
    assert lauf.fortschritt == 100
    assert lauf.ergebnis["n"] == 200


@pytest.mark.django_db
def test_run_simulation_faengt_fehler_ab():
    # Szenario ohne Faktoren -> pyfair kann nicht rechnen -> Status FEHLER.
    pytest.importorskip("pyfair")
    s = Szenario.objects.create(name="Leer", n_simulations=100)
    lauf = Simulationslauf.objects.create(szenario=s, n_simulations=100, random_seed=42)

    services._run_simulation(lauf.pk)

    lauf.refresh_from_db()
    assert lauf.status == Simulationslauf.Status.FEHLER
    assert lauf.fehler_text != ""

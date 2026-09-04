"""Tests für die CAM-Monte-Carlo-Engine + Runner (Phase 5.2)."""

import pytest

from apps.cam import services
from apps.cam.beispiele import RANSOMWARE_BEISPIEL
from apps.cam.models import CamControl, CamSimulationslauf, CamStage, CamSzenario, CamVerlustklasse


def _szenario_ransomware():
    b = RANSOMWARE_BEISPIEL
    s = CamSzenario.objects.create(**b["szenario"])
    CamControl.objects.create(szenario=s, **b["control"])
    for stage in b["stages"]:
        CamStage.objects.create(szenario=s, **stage)
    for vk in b["verlustklassen"]:
        CamVerlustklasse.objects.create(szenario=s, **vk)
    return s


@pytest.mark.django_db
def test_simuliere_cam_liefert_kennzahlen_und_lec():
    pytest.importorskip("pyfair_cam")
    s = _szenario_ransomware()

    ergebnis = services.simuliere_cam(s, n_simulations=500, random_seed=42)

    assert ergebnis["n"] == 500
    for key in ("mittelwert", "median", "min", "max", "p90", "p95", "p99", "lec", "verteilung_hist"):
        assert key in ergebnis
    assert ergebnis["min"] <= ergebnis["median"] <= ergebnis["max"]
    assert ergebnis["p90"] <= ergebnis["p99"]
    assert len(ergebnis["lec"]) > 0
    assert ergebnis["lec"][0]["ueberschreitung"] >= ergebnis["lec"][-1]["ueberschreitung"]


@pytest.mark.django_db
def test_simuliere_cam_liefert_outcome_verteilung():
    pytest.importorskip("pyfair_cam")
    s = _szenario_ransomware()

    ergebnis = services.simuliere_cam(s, n_simulations=500, random_seed=42)

    verteilung = ergebnis["outcome_verteilung"]
    assert sum(verteilung["anzahl"]) == 500
    assert set(verteilung["klassen"]) <= {"early", "mid", "late", "full_impact", "attacker_fails"}


@pytest.mark.django_db
def test_simuliere_cam_liefert_stage_erkennung_und_mittelwerte():
    pytest.importorskip("pyfair_cam")
    s = _szenario_ransomware()

    ergebnis = services.simuliere_cam(s, n_simulations=500, random_seed=42)

    stufe = ergebnis["stage_erkennung"]
    assert stufe["stufe"] == [1, 2, 3, 4, 5, 6]
    assert len(stufe["anteil"]) == 6
    assert sum(stufe["anteil"]) <= 1.0
    assert all(0.0 <= a <= 1.0 for a in stufe["anteil"])

    for feld in ("tef_mittel", "susceptibility_mittel", "lef_mittel"):
        assert ergebnis[feld] > 0


@pytest.mark.django_db
def test_run_cam_simulation_setzt_lauf_auf_fertig():
    pytest.importorskip("pyfair_cam")
    s = _szenario_ransomware()
    lauf = CamSimulationslauf.objects.create(szenario=s, n_simulations=500, random_seed=42)

    services._run_cam_simulation(lauf.pk)  # synchron, ohne Thread

    lauf.refresh_from_db()
    assert lauf.status == CamSimulationslauf.Status.FERTIG
    assert lauf.fortschritt == 100
    assert lauf.ergebnis["n"] == 500


@pytest.mark.django_db
def test_run_cam_simulation_faengt_fehler_ab():
    # Szenario ohne Control -> _build_model kann nicht rechnen -> Status FEHLER.
    pytest.importorskip("pyfair_cam")
    b = RANSOMWARE_BEISPIEL
    s = CamSzenario.objects.create(**b["szenario"])
    for stage in b["stages"]:
        CamStage.objects.create(szenario=s, **stage)
    for vk in b["verlustklassen"]:
        CamVerlustklasse.objects.create(szenario=s, **vk)
    lauf = CamSimulationslauf.objects.create(szenario=s, n_simulations=500, random_seed=42)

    services._run_cam_simulation(lauf.pk)

    lauf.refresh_from_db()
    assert lauf.status == CamSimulationslauf.Status.FEHLER
    assert lauf.fehler_text != ""
